import time
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Max, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from drill.forms import QuestionForm
from drill.models import Question
from tag.models import Tag

SECTION = "Drill"

EASY_BONUS = 1.3

# Starting "easiness" factor
# Answering "Good" will increase the delay by approximately this amount
EFACTOR_DEFAULT = 2.5

# Multiplication factor for interval
# 1.0 does nothing
# 0.8 sets the interval at 80% their normal size
INTERVAL_MODIFIER = 1.0


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
        context["section"] = SECTION
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
                          .filter(question__user=self.request.user)


@method_decorator(login_required, name='dispatch')
class DrillSearchListView(ListView):

    template_name = 'drill/search.html'

    def get_queryset(self):
        search_term = self.request.GET['search_term']

        return Question.objects.filter(Q(question__icontains=search_term) |
                                       Q(answer__icontains=search_term))

    def get_context_data(self, **kwargs):
        context = super(DrillSearchListView, self).get_context_data(**kwargs)

        info = []

        for question in context['object_list']:
            info.append(dict(tags=", ".join([x.name for x in question.tags.all()]),
                             id=question.id,
                             question=question.question,
                             answer=question.answer))

        context['cols'] = ['tags', 'id', 'question', 'answer']
        context['section'] = SECTION
        context['info'] = info
        context['title'] = 'Drill Search'
        return context


@method_decorator(login_required, name='dispatch')
class QuestionCreateView(CreateView):
    template_name = 'drill/question_edit.html'
    form_class = QuestionForm

    def get_context_data(self, **kwargs):
        context = super(QuestionCreateView, self).get_context_data(**kwargs)

        context['section'] = SECTION
        context['action'] = 'Add'
        context['title'] = 'Drill :: Add Question'
        return context

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.efactor = EFACTOR_DEFAULT
        obj.save()

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)

        obj.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('question_add')


@method_decorator(login_required, name='dispatch')
class QuestionDeleteView(DeleteView):
    template_name = 'todo/edit.html'
    form_class = QuestionForm
    model = Question

    def get_object(self, queryset=None):
        question = Question.objects.get(user=self.request.user, id=self.kwargs.get('pk'))
        return question

    def get_success_url(self):
        return reverse('question_add')


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

        context['section'] = SECTION
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

    def get_context_data(self, **kwargs):
        context = super(QuestionUpdateView, self).get_context_data(**kwargs)
        context['action'] = 'Edit'
        context['title'] = 'Drill :: Question Edit'
        return context

    def form_valid(self, form):

        obj = form.save(commit=False)

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)
        obj.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('drill_list')


@login_required
def study_tag(request, tag):

    # Criteria for selecting a question:
    #  The question hasn't been reviewed within its interval
    #  The question is new (last_reviewed is null)
    #  The question is still being learned

    try:
        question = Question.objects.filter(
            Q(user=request.user),
            Q(tags__name=tag),
            Q(interval__lte=timezone.now() - F("last_reviewed"))
            | Q(last_reviewed__isnull=True)
            | Q(state="L")
        ).order_by("?")[0]

    except IndexError:
        question = Question.objects.filter(user=request.user, tags__name=tag).order_by('?')[0]
        messages.add_message(request, messages.INFO, 'Nothing to drill. Here''s a random question.')

    return redirect('question_detail', question_id=question.id)


@login_required
def show_answer(request, question_id):

    question = Question.objects.get(user=request.user, pk=question_id)

    question.last_reviewed = timezone.now()
    question.save()

    return render(request, 'drill/answer.html',
                  {'section': SECTION,
                   'question': question,
                   'state_name': Question.get_state_name(question.state),
                   'tag_list': ", ".join([x.name for x in question.tags.all()]),
                   'learning_step_count': question.get_learning_step_count(),
                   'title': 'Drill :: Show Answer'})


@login_required
def record_result(request, question_id, result):

    question = Question.objects.get(user=request.user, pk=question_id)

    if result == 'good':
        if question.state == 'L':
            if question.is_final_learning_step():
                question.state = 'R'
            else:
                question.learning_step_increase()
        else:
            question.interval = question.interval * question.efactor
    elif result == 'easy':
        # An "easy" answer to a "Learning" question is
        #  graduated to "To Review"
        if question.state == 'L':
            question.state = 'R'
        question.interval = question.interval * EASY_BONUS * INTERVAL_MODIFIER
        question.efactor = question.efactor + (question.efactor * 0.15)
    elif result == 'hard':
        question.times_failed = question.times_failed + 1
        question.interval = question.interval * 1.2 * INTERVAL_MODIFIER
        question.efactor = question.efactor - (question.efactor * 0.15)
    elif result == 'again':
        if question.state == 'L':
            question.learning_step = 1
        else:
            question.state = 'L'
        question.interval = timedelta(days=1)
        question.efactor = question.efactor - (question.efactor * 0.2)

    question.save()

    return redirect('study_tag', tag=question.tags.all()[0].name)


def tag_search(request):

    tags = Tag.objects.filter(question__user=request.user, name__icontains=request.GET.get("query", ""), question__isnull=False).distinct("name")

    return JsonResponse([{"value": x.name, "is_meta": x.is_meta} for x in tags], safe=False)
