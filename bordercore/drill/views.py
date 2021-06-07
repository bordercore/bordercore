import re
from urllib.parse import unquote

from elasticsearch import Elasticsearch

from django import urls
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from accounts.models import SortOrderDrillTag
from bookmark.models import Bookmark
from drill.forms import QuestionForm
from lib.util import parse_title_from_url
from tag.models import Tag

from .models import EFACTOR_DEFAULT, Question, SortOrderDrillBookmark


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
            "tags_still_learning": Question.objects.tags_still_learning(self.request.user)[:10],
            "tags_needing_review": Question.objects.tags_needing_review(self.request.user)[:10],
            "random_tag": Question.objects.get_random_tag(self.request.user),
            "favorite_questions_progress": Question.objects.favorite_questions_progress(self.request.user),
            "total_progress": Question.objects.total_tag_progress(self.request.user),
            "study_session_progress": Question.get_study_session_progress(self.request.session)
        }


@method_decorator(login_required, name="dispatch")
class DrillSearchListView(ListView):

    template_name = "drill/search.html"

    def get_queryset(self):
        search_term = self.request.GET["search"]

        return Question.objects.filter(Q(question__icontains=search_term)
                                       | Q(answer__icontains=search_term)) \
                               .prefetch_related("tags")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search_term = self.request.GET["search"]

        info = []

        for question in context["object_list"]:
            info.append(dict(tags=", ".join([x.name for x in question.tags.all()]),
                             uuid=question.uuid,
                             question=re.sub("[\n\r\"]", "", question.question),
                             answer=re.sub("[\n\r\"]", "", question.answer)))

        return {
            **context,
            "cols": ["tags", "uuid", "question", "answer"],
            "search": search_term,
            "info": info,
            "title": "Drill Search"
        }


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
                    "classes": "badge badge-info",
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

        return {
            **context,
            "tag_info": self.object.get_all_tags_progress(),
            "question": self.object,
            "state_name": Question.get_state_name(self.object.state),
            "learning_step_count": self.object.get_learning_step_count(),
            "title": "Drill :: Question Detail",
            "tag_list": ", ".join([x.name for x in self.object.tags.all()]),
            "study_session_progress": Question.get_study_session_progress(self.request.session)
        }


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
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('drill:list')


@login_required
def start_study_session(request, session_type, param=None):
    """
    Start a study session
    """

    first_question = Question.start_study_session(request.user, request.session, session_type, param)

    if first_question:
        return redirect("drill:detail", uuid=first_question)
    else:
        messages.add_message(
            request,
            messages.WARNING, "No questions found to study"
        )
        return redirect("drill:list")


@login_required
def get_next_question(request):

    if "drill_study_session" in request.session:
        request.session.modified = True

        current_index = request.session["drill_study_session"]["list"].index(request.session["drill_study_session"]["current"])
        if current_index + 1 == len(request.session["drill_study_session"]["list"]):
            messages.add_message(request, messages.INFO, "Study session over.")
            request.session.pop("drill_study_session")
            return redirect("drill:list")
        next_index = current_index + 1
        next_question = request.session["drill_study_session"]["list"][next_index]
        request.session["drill_study_session"]["current"] = next_question
        return redirect("drill:detail", uuid=next_question)

    else:

        return redirect("drill:list")


@login_required
def get_current_question(request):

    if "drill_study_session" in request.session:
        current_question = request.session["drill_study_session"]["current"]
        return redirect("drill:detail", uuid=current_question)
    else:
        return redirect("drill:list")


@login_required
def start_study_session_tag(request, tag):
    return start_study_session(request, "tag-needing-review", tag)


@login_required
def start_study_session_random(request, count):
    return start_study_session(request, "random", count)


@login_required
def start_study_session_search(request, search):
    return start_study_session(request, "search", search)


@login_required
def show_answer(request, uuid):

    question = Question.objects.get(user=request.user, uuid=uuid)

    return render(request, "drill/answer.html",
                  {
                      "question": question,
                      "state_name": Question.get_state_name(question.state),
                      "tag_list": ", ".join([x.name for x in question.tags.all()]),
                      "learning_step_count": question.get_learning_step_count(),
                      "title": "Drill :: Show Answer",
                      "study_session_progress": Question.get_study_session_progress(request.session)
                  }
    )


@login_required
def record_response(request, uuid, response):

    question = Question.objects.get(user=request.user, uuid=uuid)
    question.record_response(response)

    return get_next_question(request)


@login_required
def search_tags(request):

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    search_term = request.GET["query"].lower()

    search_terms = re.split(r"\s+", unquote(search_term))

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": request.user.id
                        }
                    },
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

    # Separate query into terms based on whitespace and
    #  and treat it like an "AND" boolean search
    for one_term in search_terms:
        search_object["query"]["bool"]["must"].append(
            {
                "bool": {
                    "should": [
                        {
                            "wildcard": {
                                "tags": {
                                    "value": f"*{one_term}*",
                                }
                            }
                        }
                    ]
                }
            }
        )

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
                "info": Question.get_tag_progress(request.user, tag_result["key"]),
                "link": reverse("drill:start_study_session_tag", kwargs={"tag": tag_result["key"]})
            }
            )

    return JsonResponse(matches, safe=False)


@login_required
def get_pinned_tags(request):

    tags = Question.objects.get_pinned_tags(request.user)

    response = {
        "status": "OK",
        "tag_list": tags
    }

    return JsonResponse(response)


@login_required
def pin_tag(request):

    tag_name = request.POST["tag"]

    if SortOrderDrillTag.objects.filter(userprofile=request.user.userprofile, tag__name=tag_name).exists():

        response = {
            "status": "Error",
            "message": "Duplicate: that tag is already pinned."
        }

    else:

        tag = Tag.objects.get(name=tag_name, user=request.user)
        so = SortOrderDrillTag(userprofile=request.user.userprofile, tag=tag)
        so.save()

        response = {
            "status": "OK"
        }

    return JsonResponse(response)


@login_required
def is_favorite_mutate(request):

    question_uuid = request.POST["question_uuid"]
    mutation = request.POST["mutation"]

    question = Question.objects.get(uuid=question_uuid)

    if mutation == "add":
        question.is_favorite = True
    elif mutation == "delete":
        question.is_favorite = False

    question.save()

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def get_bookmark_list(request, uuid):

    question = Question.objects.get(uuid=uuid, user=request.user)
    bookmark_list = list(question.bookmarks.all().only("name", "id").order_by("sortorderdrillbookmark__sort_order"))

    response = {
        "status": "OK",
        "bookmark_list": [
            {
                "name": x.name,
                "url": x.url,
                "id": x.id,
                "uuid": x.uuid,
                "favicon_url": x.get_favicon_url(size=16),
                "note": x.sortorderdrillbookmark_set.get(question=question).note,
                "edit_url": reverse("bookmark:update", kwargs={"uuid": x.uuid})
            }
            for x
            in bookmark_list]
    }

    return JsonResponse(response)


@login_required
def sort_bookmark_list(request):
    """
    Move a given bookmark to a new position in a sorted list
    """

    question_uuid = request.POST["question_uuid"]
    bookmark_uuid = request.POST["bookmark_uuid"]
    new_position = int(request.POST["new_position"])

    so = SortOrderDrillBookmark.objects.get(question__uuid=question_uuid, bookmark__uuid=bookmark_uuid)
    SortOrderDrillBookmark.reorder(so, new_position)

    so.question.modified = timezone.now()
    so.question.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def add_bookmark(request):

    question_uuid = request.POST["question_uuid"]
    bookmark_uuid = request.POST["bookmark_uuid"]

    question = Question.objects.get(uuid=question_uuid, user=request.user)
    bookmark = Bookmark.objects.get(uuid=bookmark_uuid)

    so = SortOrderDrillBookmark(question=question, bookmark=bookmark)
    so.save()

    so.question.modified = timezone.now()
    so.question.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def remove_bookmark(request):

    question_uuid = request.POST["question_uuid"]
    bookmark_uuid = request.POST["bookmark_uuid"]

    so = SortOrderDrillBookmark.objects.get(question__uuid=question_uuid, bookmark__uuid=bookmark_uuid)
    so.delete()

    so.question.modified = timezone.now()
    so.question.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def edit_bookmark_note(request):

    question_uuid = request.POST["question_uuid"]
    bookmark_uuid = request.POST["bookmark_uuid"]
    note = request.POST["note"]

    so = SortOrderDrillBookmark.objects.get(question__uuid=question_uuid, bookmark__uuid=bookmark_uuid)
    so.note = note
    so.save()

    so.question.modified = timezone.now()
    so.question.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def get_title_from_url(request):

    url = unquote(request.GET["url"])

    message = ""
    title = None
    bookmark_uuid = None

    url_info = Bookmark.objects.filter(url=url, user=request.user)
    if url_info:
        title = url_info[0].name
        message = "Existing bookmark found in Bordercore."
        bookmark_uuid = url_info[0].uuid
    else:
        try:
            title = parse_title_from_url(url)[1]
            message = "Bookmark not found in Bordercore."
        except Exception as e:
            message = str(e)

    response = {
        "status": "OK",
        "title": title,
        "bookmarkUuid": bookmark_uuid,
        "message": message
    }

    return JsonResponse(response)
