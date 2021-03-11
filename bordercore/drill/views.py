import time

from elasticsearch import Elasticsearch

from django import urls
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count, F, Max, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from accounts.models import SortOrderDrillTag
from drill.forms import QuestionForm
from drill.models import EFACTOR_DEFAULT, Question
from tag.models import Tag


@method_decorator(login_required, name='dispatch')
class DrillListView(ListView):

    template_name = "drill/drill_list.html"
    queryset = Question.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return {
            **context,
            "cols": ["tag_name", "question_count", "last_reviewed", "lastreviewed_sort", "id"],
            "title": "Home",
            "tags_still_learning": Question.get_tags_still_learning(self.request.user),
            "tags_needing_review": Question.get_tags_needing_review(self.request.user),
            "random_tag": Question.get_random_tag(self.request.user),
            "total_progress": Question.get_total_progress(self.request.user),
            "no_left_block": True,
            "content_block_width": "12"
        }


@method_decorator(login_required, name='dispatch')
class DrillSearchListView(ListView):

    template_name = 'drill/search.html'

    def get_queryset(self):
        search_term = self.request.GET['search']

        return Question.objects.filter(Q(question__icontains=search_term)
                                       | Q(answer__icontains=search_term))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search_term = self.request.GET['search']

        info = []

        for question in context['object_list']:
            info.append(dict(tags=", ".join([x.name for x in question.tags.all()]),
                             uuid=question.uuid,
                             question=question.question,
                             answer=question.answer))

        context['cols'] = ['tags', 'uuid', 'question', 'answer']
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
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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

        review_url = urls.reverse("drill:detail", kwargs={"uuid": obj.uuid})
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
        return super().delete(request, *args, **kwargs)

    def get_object(self, queryset=None):
        question = Question.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        return question

    def get_success_url(self):
        return reverse('drill:add')


@method_decorator(login_required, name='dispatch')
class QuestionDetailView(DetailView):

    model = Question
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    template_name = 'drill/question.html'

    def get_object(self, queryset=None):
        obj = Question.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['tag_info'] = self.object.get_tags_info()
        context['question'] = self.object
        context['state_name'] = Question.get_state_name(self.object.state)
        context['learning_step_count'] = self.object.get_learning_step_count()
        context['title'] = 'Drill :: Question Detail'
        context['tag_list'] = ", ".join([x.name for x in self.object.tags.all()])
        context["no_left_block"] = True
        context["content_block_width"] = "12"

        return context


@method_decorator(login_required, name='dispatch')
class QuestionUpdateView(UpdateView):
    model = Question
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    form_class = QuestionForm
    template_name = 'drill/question_edit.html'

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in QuestionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

        review_url = urls.reverse("drill:detail", kwargs={"uuid": obj.uuid})
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
    return redirect("drill:detail", uuid=question.uuid)


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

    return redirect('drill:detail', uuid=question.uuid)


@login_required
def show_answer(request, uuid):

    question = Question.objects.get(user=request.user, uuid=uuid)

    return render(request, 'drill/answer.html',
                  {'question': question,
                   'state_name': Question.get_state_name(question.state),
                   'tag_list': ", ".join([x.name for x in question.tags.all()]),
                   'learning_step_count': question.get_learning_step_count(),
                   'no_left_block': True,
                   'content_block_width': '12',
                   'title': 'Drill :: Show Answer'})


@login_required
def record_response(request, uuid, response):

    question = Question.objects.get(user=request.user, uuid=uuid)
    question.last_reviewed = timezone.now()
    question.record_response(response)

    if request.session.get("drill_mode") == "random":
        return redirect("drill:study_random")
    else:
        return redirect("drill:study_tag", tag=question.tags.all().first().name)


@login_required
def skip_question(request, uuid):

    question = Question.objects.get(user=request.user, uuid=uuid)

    if request.session.get("drill_mode") == "random":
        return redirect("drill:study_random")
    else:
        return redirect("drill:study_tag", tag=question.tags.all().first().name)


@login_required
def search_tags(request):

    search_term = request.GET["query"].lower()

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": request.user.id
                        }
                    },
                    {
                        "wildcard": {
                            "tags": f"{search_term}*"
                        }
                    }
                ]
            }
        },
        "aggs": {
            "Distinct Tags": {
                "terms": {
                    "field": "tags.keyword",
                    "size": 1000
                }
            }
        },
        "from": 0, "size": 0,
        "_source": ["tags"]
    }

    # If "drill_only" is passed in, then limit our search
    #  to tags attached to questions, rather than all tags
    if "drill_only" in request.GET:
        search_object["query"]["bool"]["must"].append(
            {
                "term": {
                    "doctype": "drill"
                }
            },
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    matches = []
    for tag_result in results["aggregations"]["Distinct Tags"]["buckets"]:
        if tag_result["key"].lower().find(search_term.lower()) != -1:
            matches.append({
                "value": tag_result["key"],
                "id": tag_result["key"],
                "info": Question.get_tag_info(request.user, tag_result["key"]),
                "link": reverse("drill:study_tag", kwargs={"tag": tag_result["key"]})
            }
            )

    return JsonResponse(matches, safe=False)


@login_required
def get_favorite_tags(request):

    tags = Question.get_favorite_tags(request.user)

    response = {
        "status": "OK",
        "tag_list": tags
    }

    return JsonResponse(response)


@login_required
def add_favorite_tag(request):

    tag_name = request.POST["tag"]

    if SortOrderDrillTag.objects.filter(userprofile=request.user.userprofile, tag__name=tag_name).exists():

        response = {
            "status": "Error",
            "message": "Duplicate: that tag is already a favorite."
        }

    else:

        tag = Tag.objects.get(name=tag_name, user=request.user)
        so = SortOrderDrillTag(userprofile=request.user.userprofile, tag=tag)
        so.save()

        response = {
            "status": "OK"
        }

    return JsonResponse(response)
