import time
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Max, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import (CreateView, DeleteView, FormMixin,
                                       UpdateView)
from django.views.generic.list import ListView
from drill.forms import DeckForm, QuestionForm
from drill.models import Deck, Question
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
class DeckCreateView(CreateView):
    template_name = "drill/deck_list.html"
    form_class = DeckForm

    def get_context_data(self, **kwargs):
        context = super(DeckCreateView, self).get_context_data(**kwargs)
        context["action"] = "Add"
        return context

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()

        obj.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("deck_list")


@method_decorator(login_required, name='dispatch')
class DeckDetailView(DetailView):

    model = Deck
    slug_field = "id"
    slug_url_kwarg = "deck_id"

    def get_context_data(self, **kwargs):
        context = super(DeckDetailView, self).get_context_data(**kwargs)

        context["section"] = SECTION
        context["count"] = Question.objects.filter(user=self.request.user, deck_id=self.object.id).count()
        state_counts = []
        for state in Question.objects.filter(user=self.request.user, deck=self.object).values("state").annotate(state_count=Count("state")).order_by("state_count"):
            state_counts.append([Question.get_state_name(state["state"]), state["state_count"]])
        context["state_counts"] = state_counts
        context["title"] = "Deck Detail :: {}".format(self.object.title)
        return context

    def get_queryset(self):
        return Deck.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class DeckListView(ListView):

    context_object_name = "info"
    template_name = "drill/deck_list.html"

    def get_context_data(self, **kwargs):
        context = super(DeckListView, self).get_context_data(**kwargs)

        info = []

        for deck in self.object_list:
            if deck["max"]:
                last_reviewed = deck["max"].strftime("%b %d, %Y")
                last_reviewed_sort = time.mktime(deck["max"].timetuple())
            else:
                last_reviewed = ""
                last_reviewed_sort = ""
            info.append(dict(tag_name=deck["name"],
                             question_count=deck["count"],
                             last_reviewed=last_reviewed,
                             lastreviewed_sort=last_reviewed_sort,
                             id=deck["id"]))

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
class DeckSearchListView(ListView):

    template_name = 'drill/search.html'

    def get_queryset(self):
        search_term = self.request.GET['search_term']

        return Question.objects.filter(Q(question__icontains=search_term) |
                                       Q(answer__icontains=search_term))

    def get_context_data(self, **kwargs):
        context = super(DeckSearchListView, self).get_context_data(**kwargs)

        info = []

        for myobject in context['object_list']:
            info.append(dict(deck_title=myobject.deck.title,
                             id=myobject.id,
                             question=myobject.question,
                             answer=myobject.answer,
                             deck_id=myobject.deck.id))

        context['cols'] = ['deck_title', 'id', 'question', 'answer', 'deck_id']
        context['section'] = SECTION
        context['info'] = info
        context['title'] = 'Drill Search'
        return context


@method_decorator(login_required, name='dispatch')
class DeckUpdateView(UpdateView):
    model = Deck
    form_class = DeckForm
    success_url = reverse_lazy('deck_list')

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user

        obj.save()

        return HttpResponseRedirect(self.get_success_url())


@method_decorator(login_required, name='dispatch')
class DeckDeleteView(DeleteView):

    def get_object(self, queryset=None):
        return Deck.objects.get(user=self.request.user, id=self.kwargs.get("pk"))

    def get_success_url(self):
        return reverse("deck_list")


@method_decorator(login_required, name='dispatch')
class QuestionCreateView(CreateView):
    template_name = 'drill/question_edit.html'
    form_class = QuestionForm

    def get_context_data(self, **kwargs):
        context = super(QuestionCreateView, self).get_context_data(**kwargs)
        context['action'] = 'Add'
        context['deck'] = Deck.objects.get(user=self.request.user, pk=self.kwargs['deck_id'])
        context['title'] = 'Drill :: Add Question'
        return context

    def form_valid(self, form):

        self.deck_id = self.request.POST['deck_id']

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.deck_id = self.deck_id
        obj.efactor = EFACTOR_DEFAULT
        obj.save()

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)

        obj.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('deck_detail', kwargs={'deck_id': self.deck_id})


@method_decorator(login_required, name='dispatch')
class QuestionDeleteView(DeleteView):
    template_name = 'todo/edit.html'
    form_class = QuestionForm
    model = Question

    def get_object(self, queryset=None):
        question = Question.objects.get(user=self.request.user, id=self.kwargs.get('pk'))
        self.deck_id = question.deck_id
        return question

    def get_success_url(self):
        return reverse('deck_detail', kwargs={'deck_id': self.deck_id})


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
        context['deck'] = self.object.deck
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
        context['deck'] = Deck.objects.get(user=self.request.user, pk=context['question'].deck_id)
        context['title'] = 'Drill :: Question Edit'
        return context

    def form_valid(self, form):

        self.deck_id = self.request.POST['deck_id']

        obj = form.save(commit=False)

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)
        obj.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('deck_detail', kwargs={'deck_id': self.deck_id})


@login_required
def get_info(request):

    from django.core.exceptions import ObjectDoesNotExist

    info = ''

    try:
        if request.GET.get('query_type', '') == 'id':
            match = Deck.objects.get(user=request.user, pk=request.GET['id'])
        else:
            match = Deck.objects.get(user=request.user, title=request.GET['title'])
        if match:
            info = {'title': match.title,
                    'description': match.description,
                    'id': match.id}
    except ObjectDoesNotExist:
        pass

    return JsonResponse(info)


@login_required
def study_deck(request, deck_id):

    # Criteria for selecting a question:
    #  The question hasn't been reviewed within its interval
    #  The question is new (last_reviewed is null)
    #  The question is still being learned

    try:
        question = Question.objects.filter(
            Q(user=request.user),
            Q(deck__id=deck_id),
            Q(interval__lte=timezone.now() - F("last_reviewed"))
            | Q(last_reviewed__isnull=True)
            | Q(state="L")
        ).order_by("?")[0]

    except IndexError:
        question = Question.objects.filter(user=request.user, deck=deck_id).order_by('?')[0]
        messages.add_message(request, messages.INFO, 'Nothing to drill. Here''s a random question.')

    return redirect('question_detail', question_id=question.id)


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
    deck = Deck.objects.get(user=request.user, pk=question.deck.id)

    return render(request, 'drill/answer.html',
                  {'section': SECTION,
                   'deck': deck,
                   'question': question,
                   'state_name': Question.get_state_name(question.state),
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

    return redirect('deck_study', deck_id=question.deck.id)


def tag_search(request):

    tags = Tag.objects.filter(question__user=request.user, name__icontains=request.GET.get("query", ""), question__isnull=False).distinct("name")

    return JsonResponse([{"value": x.name, "is_meta": x.is_meta} for x in tags], safe=False)
