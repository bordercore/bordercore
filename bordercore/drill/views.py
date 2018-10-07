from django.db.models import Count, Max
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormMixin, UpdateView
from django.views.generic.list import ListView

from drill.forms import DeckForm, QuestionForm
from drill.models import Deck, Question

SECTION = "Drill"

EASY_BONUS = 1.3

# Starting "easiness" factor
# Answering "Good" will increase the delay by approximately this amount
EFACTOR_DEFAULT = 2.5

# Multiplication factor for interval
# 1.0 does nothing
# 0.8 sets the interval at 80% their normal size
INTERVAL_MODIFIER = 1.0


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


class DeckListView(FormMixin, ListView):

    context_object_name = "info"
    form_class = DeckForm
    model = Deck

    def get_context_data(self, **kwargs):
        context = super(DeckListView, self).get_context_data(**kwargs)

        info = []

        for deck in context['object_list']:
            info.append(dict(name=deck.title,
                             created=deck.get_created(),
                             unixtime=format(deck.created, 'U'),
                             questioncount=Question.objects.filter(user=self.request.user, deck=deck).count(),
                             id=deck.id))

        context['cols'] = ['name', 'created', 'unixtime', 'questioncount', 'id']
        context['section'] = SECTION
        context['info'] = info

        return context

#     def get_queryset(self):
#         print("get_queryset")
#         decks = Deck.objects.values('id', 'title', 'created').annotate(max=Max('question__last_reviewed')).annotate(count=Count('question'))

#         for deck in decks:
#             deck['foo'] = 'bar'
# #            print("{}, {}, {}, {}, {}".format(deck['id'], deck['title'], deck['count'], deck['created'].strftime('%b %d, %Y'),deck['max']))

#         return decks


class DeckUpdateView(UpdateView):
    model = Deck
    form_class = DeckForm
    success_url = reverse_lazy('deck_list')

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user

        obj.save()

        return HttpResponseRedirect(self.get_success_url())


class QuestionCreateView(CreateView):
    template_name = 'drill/question_edit.html'
    form_class = QuestionForm

    def get_context_data(self, **kwargs):
        context = super(QuestionCreateView, self).get_context_data(**kwargs)
        context['action'] = 'Add'
        context['deck'] = Deck.objects.get(user=self.request.user, pk=self.kwargs['deck_id'])
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


class QuestionUpdateView(UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'drill/question_edit.html'
    # success_url = reverse_lazy('deck_list')

    def get_context_data(self, **kwargs):
        context = super(QuestionUpdateView, self).get_context_data(**kwargs)
        context['action'] = 'Edit'
        context['deck'] = Deck.objects.get(user=self.request.user, pk=context['question'].deck_id)
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


def ask_question(request, deck_id):

    deck = Deck.objects.get(user=request.user, pk=deck_id)
    message = None

    # Criteria for selecting a question:
    #  The question hasn't been reviewed within its interval
    #  The question is new (last_reviewed is null)
    #  The question is still being learned

    try:
        question = Question.objects.raw("""
 select * from drill_question
 where (date_part('day', now() - last_reviewed) > interval
        or last_reviewed is null
        or state='L')
 and deck_id = %s
 and user_id = %s
 order by random()
    limit 1""", [deck_id, request.user.id])[0]
    except IndexError:
        question = Question.objects.filter(user=request.user, deck=deck_id).order_by('?')[0]
        message = 'Nothing to drill. Here''s a random question.'

    return render(request, 'drill/question.html',
                  {'section': SECTION,
                   'deck': deck,
                   'question': question,
                   'state_name': Question.get_state_name(question.state),
                   'learning_step_count': question.get_learning_step_count(),
                   'message': message})


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
                   'learning_step_count': question.get_learning_step_count()})


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
        question.interval = 1
        question.efactor = question.efactor - (question.efactor * 0.2)

    question.save()

    deck = Deck.objects.get(user=request.user, pk=question.deck.id)

    return render(request, 'drill/question.html',
                  {'section': SECTION,
                   'deck': deck,
                   'question': question,
                   'state_name': Question.get_state_name(question.state),
                   'learning_step_count': question.get_learning_step_count()})
