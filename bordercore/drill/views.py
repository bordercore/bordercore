import json
from urllib.parse import unquote

from django import urls
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from accounts.models import SortOrderDrillTag
from blob.models import Blob
from bookmark.models import Bookmark
from drill.forms import QuestionForm
from lib.mixins import FormRequestMixin
from lib.util import parse_title_from_url
from tag.models import Tag

from .models import (EFACTOR_DEFAULT, Question, SortOrderQuestionBlob,
                     SortOrderQuestionBookmark)


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
            "tags_still_learning": Question.objects.tags_still_learning(self.request.user)[:20],
            "tags_needing_review": Question.objects.tags_needing_review(self.request.user)[:20],
            "random_tag": Question.objects.get_random_tag(self.request.user),
            "favorite_questions_progress": Question.objects.favorite_questions_progress(self.request.user),
            "total_progress": Question.objects.total_tag_progress(self.request.user),
            "study_session_progress": Question.get_study_session_progress(self.request.session)
        }


@method_decorator(login_required, name='dispatch')
class QuestionCreateView(FormRequestMixin, CreateView):
    template_name = 'drill/question_edit.html'
    form_class = QuestionForm

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
                    "is_meta": tag.is_meta,
                    "classes": "badge bg-info",
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

        # Save the tags
        form.save_m2m()

        handle_related_bookmarks(obj, self.request)
        handle_related_blobs(obj, self.request)

        review_url = urls.reverse("drill:detail", kwargs={"uuid": obj.uuid})
        messages.add_message(
            self.request,
            messages.INFO, f"Question added. <a href='{review_url}'>Review it here</a>"
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('drill:add')


def handle_related_bookmarks(question, request):

    info = request.POST.get("related-bookmarks", None)

    if not info:
        return

    for bookmark_info in json.loads(info):
        bookmark = Bookmark.objects.get(uuid=bookmark_info["uuid"])
        so = SortOrderQuestionBookmark(
            question=question,
            bookmark=bookmark,
            note=bookmark_info["note"] if "note" in bookmark_info else None
        )
        so.save()


def handle_related_blobs(question, request):

    info = request.POST.get("related-blobs", None)

    if not info:
        return

    for blob_info in json.loads(info):
        blob = Blob.objects.get(uuid=blob_info["uuid"])
        so = SortOrderQuestionBlob(
            question=question,
            blob=blob,
            note=blob_info["note"]
        )
        so.save()


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


@method_decorator(login_required, name="dispatch")
class QuestionDetailView(DetailView):

    model = Question
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    template_name = "drill/question.html"

    def get_object(self, queryset=None):
        obj = Question.objects.get(user=self.request.user, uuid=self.kwargs.get("uuid"))
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
class QuestionUpdateView(FormRequestMixin, UpdateView):
    model = Question
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    form_class = QuestionForm
    template_name = 'drill/question_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        context['title'] = 'Drill :: Question Update'
        context['tags'] = [{"text": x.name, "is_meta": x.is_meta} for x in self.object.tags.all()]
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
            messages.INFO,
            f"Question edited. <a href='{review_url}'>Review it here</a>"
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):

        if "return_url" in self.request.POST:
            return self.request.POST["return_url"]
        else:
            return reverse('drill:list')


@login_required
def start_study_session(request, session_type, param=None):
    """
    Start a study session
    """
    first_question = Question.start_study_session(request.user, request.session, session_type, request.GET.get("filter", None), param)

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
def record_response(request, uuid, response):

    question = Question.objects.get(user=request.user, uuid=uuid)
    question.record_response(response)

    return get_next_question(request)


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
def unpin_tag(request):

    tag_name = request.POST["tag"]

    if not SortOrderDrillTag.objects.filter(userprofile=request.user.userprofile, tag__name=tag_name).exists():

        response = {
            "status": "Error",
            "message": "That tag is not pinned."
        }

    else:

        so = SortOrderDrillTag.objects.get(userprofile=request.user.userprofile, tag__name=tag_name)
        so.delete()

        response = {
            "status": "OK"
        }

    return JsonResponse(response)


@login_required
def sort_pinned_tags(request):
    """
    Move a given pinned tag to a new position in a sorted list
    """

    tag_name = request.POST["tag_name"]
    new_position = int(request.POST["new_position"])

    so = SortOrderDrillTag.objects.get(tag__name=tag_name, userprofile=request.user.userprofile)
    SortOrderDrillTag.reorder(so, new_position)

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
        except Exception as e:
            message = str(e)

    response = {
        "status": "OK",
        "title": title,
        "bookmarkUuid": bookmark_uuid,
        "message": message
    }

    return JsonResponse(response)


@login_required
def get_blob_list(request, uuid):

    question = Question.objects.get(uuid=uuid, user=request.user)
    blob_list = list(question.blobs.all().only("name", "id").order_by("sortorderquestionblob__sort_order"))

    response = {
        "status": "OK",
        "blob_list": [
            {
                "name": x.name,
                "uuid": x.uuid,
                "note": x.sortorderquestionblob_set.get(question=question).note,
                "url": reverse("blob:detail", kwargs={"uuid": x.uuid}),
                "cover_url": Blob.get_cover_url_static(
                    x.uuid,
                    x.file.name,
                    size="small"
                )
            }
            for x
            in blob_list]
    }

    return JsonResponse(response)


@login_required
def sort_blob_list(request):
    """
    Move a given blob to a new position in a sorted list
    """

    question_uuid = request.POST["question_uuid"]
    blob_uuid = request.POST["blob_uuid"]
    new_position = int(request.POST["new_position"])

    so = SortOrderQuestionBlob.objects.get(question__uuid=question_uuid, blob__uuid=blob_uuid)
    SortOrderQuestionBlob.reorder(so, new_position)

    so.question.modified = timezone.now()
    so.question.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def add_blob(request):

    question_uuid = request.POST["question_uuid"]
    blob_uuid = request.POST["blob_uuid"]

    response = {
        "status": "OK",
        "message": ""
    }

    if SortOrderQuestionBlob.objects.filter(question__uuid=question_uuid, blob__uuid=blob_uuid).exists():
        response = {
            "message": "Blob already related to this question",
            "status": "Warning"
        }
    else:
        question = Question.objects.get(uuid=question_uuid, user=request.user)
        blob = Blob.objects.get(uuid=blob_uuid)

        so = SortOrderQuestionBlob(question=question, blob=blob)
        so.save()

        so.question.modified = timezone.now()
        so.question.save()

    return JsonResponse(response)


@login_required
def remove_blob(request):

    question_uuid = request.POST["question_uuid"]
    blob_uuid = request.POST["blob_uuid"]

    so = SortOrderQuestionBlob.objects.get(question__uuid=question_uuid, blob__uuid=blob_uuid)
    so.delete()

    so.question.modified = timezone.now()
    so.question.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def edit_blob_note(request):

    question_uuid = request.POST["question_uuid"]
    blob_uuid = request.POST["blob_uuid"]
    note = request.POST["note"]

    so = SortOrderQuestionBlob.objects.get(question__uuid=question_uuid, blob__uuid=blob_uuid)
    so.note = note
    so.save()

    so.question.modified = timezone.now()
    so.question.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)
