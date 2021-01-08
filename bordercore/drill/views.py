import time

from django import urls
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Max, Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from drill.forms import QuestionForm
from drill.models import EFACTOR_DEFAULT, Question
from tag.models import Tag


@method_decorator(login_required, name='dispatch')
class DrillListView(ListView):

    context_object_name = "info"
    template_name = "drill/drill_list.html"

    def get_context_data(self, **kwargs):
        context = super(DrillListView, self).get_context_data(**kwargs)

        info = []

        for tag in self.object_list:
            if tag["max"]:
                last_reviewed = tag["max"].strftime("%b %d, %Y")
                last_reviewed_sort = time.mktime(tag["max"].timetuple())
            else:
                last_reviewed = ""
                last_reviewed_sort = ""
            info.append(dict(tag_name=tag["name"],
                             question_count=tag["count"],
                             last_reviewed=last_reviewed,
                             lastreviewed_sort=last_reviewed_sort,
                             id=tag["id"]))

        context["cols"] = ["tag_name", "question_count", "last_reviewed", "lastreviewed_sort", "id"]
        context["info"] = info
        context["title"] = "Tag Categories"
        return context

    def get_queryset(self):
        # TODO: This query joins on drill_question_tags *twice*, which is
        #  obviously inefficient. The "distinct=True" saves us for now
        #  from returning duplicate rows
        return Tag.objects.values("id", "name") \
                          .annotate(count=Count("question", distinct=True)) \
                          .annotate(max=Max("question__last_reviewed")) \
                          .filter(user=self.request.user, question__user=self.request.user)


@method_decorator(login_required, name='dispatch')
class DrillSearchListView(ListView):

    template_name = 'drill/search.html'

    def get_queryset(self):
        search_term = self.request.GET['search']

        return Question.objects.filter(Q(question__icontains=search_term)
                                       | Q(answer__icontains=search_term))

    def get_context_data(self, **kwargs):
        context = super(DrillSearchListView, self).get_context_data(**kwargs)

        search_term = self.request.GET['search']

        info = []

        for question in context['object_list']:
            info.append(dict(tags=", ".join([x.name for x in question.tags.all()]),
                             id=question.id,
                             question=question.question,
                             answer=question.answer))

        context['cols'] = ['tags', 'id', 'question', 'answer']
        context['search'] = search_term
        context['info'] = info
        context['title'] = 'Drill Search'
        return context


@method_decorator(login_required, name='dispatch')
class QuestionCreateView(CreateView):
    template_name = 'drill/question_edit.html'
    form_class = QuestionForm

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in QuestionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super(QuestionCreateView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(QuestionCreateView, self).get_context_data(**kwargs)

        context['action'] = 'Add'
        context['title'] = 'Drill :: Add Question'

        # If we're adding a question with an initial tag value,
        # pre-populate the form with this tag.
        if context['form']['tags'].value():
            tag = Tag.objects.get(user=self.request.user, name=context['form']['tags'].value())
            context['tags'] = [
                {
                    "text": tag.name,
                    "value": tag.name,
                    "is_meta": tag.is_meta,
                    "classes": "badge badge-primary",
                }
            ]

        return context

    def get_initial(self):
        tag = self.kwargs.get('tag')
        if tag:
            return {"tags": tag}

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.efactor = EFACTOR_DEFAULT
        obj.save()

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)

        obj.save()

        review_url = urls.reverse("drill:detail", kwargs={"question_id": obj.id})
        messages.add_message(
            self.request,
            messages.INFO, f"Question added. <a href='{review_url}'>Review it here</a>"
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('drill:add')


@method_decorator(login_required, name='dispatch')
class QuestionDeleteView(DeleteView):

    form_class = QuestionForm
    model = Question

    def delete(self, request, *args, **kwargs):
        messages.add_message(self.request, messages.INFO, "Question deleted")
        return super(QuestionDeleteView, self).delete(request, *args, **kwargs)

    def get_object(self, queryset=None):
        question = Question.objects.get(user=self.request.user, id=self.kwargs.get('pk'))
        return question

    def get_success_url(self):
        return reverse('drill:add')


@method_decorator(login_required, name='dispatch')
class QuestionDetailView(DetailView):

    model = Question
    slug_field = 'id'
    slug_url_kwarg = 'id'
    template_name = 'drill/question.html'

    def get_object(self, queryset=None):
        obj = Question.objects.get(user=self.request.user, id=self.kwargs.get('question_id'))
        return obj

    def get_context_data(self, **kwargs):
        context = super(QuestionDetailView, self).get_context_data(**kwargs)

        context['question'] = self.object
        context['state_name'] = Question.get_state_name(self.object.state)
        context['learning_step_count'] = self.object.get_learning_step_count()
        context['title'] = 'Drill :: Question Detail'
        context['tag_list'] = ", ".join([x.name for x in self.object.tags.all()])

        return context


@method_decorator(login_required, name='dispatch')
class QuestionUpdateView(UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'drill/question_edit.html'

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in QuestionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super(QuestionUpdateView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(QuestionUpdateView, self).get_context_data(**kwargs)
        context['action'] = 'Update'
        context['title'] = 'Drill :: Question Update'
        context['tags'] = [{"text": x.name, "value": x.name, "is_meta": x.is_meta} for x in self.object.tags.all()]
        return context

    def form_valid(self, form):

        # Delete all existing tags
        form.instance.tags.clear()

        obj = form.save(commit=False)

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)
        obj.save()

        review_url = urls.reverse("drill:detail", kwargs={"question_id": obj.id})
        messages.add_message(
            self.request,
            messages.INFO, f"Question edited. <a href='{review_url}'>Review it here</a>",
            extra_tags="show_in_dom"
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('drill:list')


@login_required
def study_random(request):

    request.session["drill_mode"] = "random"
    question = Question.objects.filter(user=request.user).order_by("?").first()
    return redirect("drill:detail", question_id=question.id)


@login_required
def study_tag(request, tag):

    request.session.pop("drill_mode", None)

    # Criteria for selecting a question:
    #  The question hasn't been reviewed within its interval
    #  The question is new (last_reviewed is null)
    #  The question is still being learned
    question = Question.objects.filter(
        Q(user=request.user),
        Q(tags__name=tag),
        Q(interval__lte=timezone.now() - F("last_reviewed"))
        | Q(last_reviewed__isnull=True)
        | Q(state="L")
    ).order_by("?").first()

    if question is None:
        question = Question.objects.filter(user=request.user, tags__name=tag).order_by('?').first()
        messages.add_message(request, messages.INFO, 'Nothing to drill. Here''s a random question.')

    return redirect('drill:detail', question_id=question.id)


@login_required
def show_answer(request, question_id):

    question = Question.objects.get(user=request.user, pk=question_id)

    return render(request, 'drill/answer.html',
                  {'question': question,
                   'state_name': Question.get_state_name(question.state),
                   'tag_list': ", ".join([x.name for x in question.tags.all()]),
                   'learning_step_count': question.get_learning_step_count(),
                   'title': 'Drill :: Show Answer'})


@login_required
def record_response(request, question_id, response):

    question = Question.objects.get(user=request.user, pk=question_id)
    question.last_reviewed = timezone.now()
    question.record_response(response)

    if request.session.get("drill_mode") == "random":
        return redirect("drill:study_random")
    else:
        return redirect("drill:study_tag", tag=question.tags.all().first().name)


@login_required
def skip_question(request, question_id):

    question = Question.objects.get(user=request.user, pk=question_id)

    if request.session.get("drill_mode") == "random":
        return redirect("drill:study_random")
    else:
        return redirect("drill:study_tag", tag=question.tags.all().first().name)
