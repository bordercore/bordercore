import datetime
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Max, OuterRef, Subquery
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView

from fitness.models import Data, Exercise, ExerciseUser

SECTION = 'Fitness'


@method_decorator(login_required, name='dispatch')
class ExerciseDetailView(DetailView):

    model = Exercise
    slug_field = 'id'
    slug_url_kwarg = 'exercise_id'

    def get_context_data(self, **kwargs):
        context = super(ExerciseDetailView, self).get_context_data(**kwargs)
        context['id'] = self.object.id
        try:
            workout_data = Data.objects.filter(user=self.request.user, exercise__id=self.object.id).order_by('-date')[:70]
            context['recent_data'] = workout_data[0]
            context['delta_days'] = int((int(datetime.datetime.now().strftime("%s")) - int(context['recent_data'].date.strftime("%s"))) / 86400) + 1
        except IndexError:
            pass
        context['activity_info'] = ExerciseUser.objects.filter(user=self.request.user, exercise__id=self.object.id)
        context['section'] = SECTION
        context['title'] = 'Exercise Detail :: {}'.format(self.object.exercise)
        self.set_plot_data(context, workout_data)
        return context

    def set_plot_data(self, context, data):

        plotdata = []
        current_workout = None
        reps = []
        labels = []

        for d in data:
            day = int(int(d.date.strftime("%s")) / 86400)
            if current_workout is not None:
                if day != int(int(current_workout.date.strftime("%s")) / 86400):
                    labels.append(current_workout.date.strftime("%b %d"))
                    plotdata.append(current_workout.weight)
                    if not context.get('reps', ''):
                        context['first_reps'] = reps[-1]
                        context['reps'] = ", ".join(str(x) for x in reversed(reps))
                    reps = []
                    current_workout = d
            else:
                current_workout = d
            reps.append(d.reps)
        context['labels'] = json.dumps(labels[::-1])
        context['plotdata'] = json.dumps(plotdata[::-1])


@login_required
def fitness_add(request, exercise_id):

    exercise = Exercise.objects.get(pk=exercise_id)

    if request.method == 'POST':
        for datum in json.loads(request.POST['workout-data']):
            new_data = Data(weight=datum[0], reps=datum[1], user=request.user, exercise=exercise)
            new_data.save()
        messages.add_message(request, messages.INFO, 'Added workout data for exercise <strong>%s</strong>' % exercise)

    return redirect('fitness_summary')


@login_required
def fitness_summary(request):

    newest = ExerciseUser.objects.filter(exercise=OuterRef("pk")) \
        .filter(user=request.user)

    # TODO: The following queries is not performant. Optimize!
    exercises = Exercise.objects.annotate(
        last_active=Max("data__date"), is_active=Subquery(newest.values("started")[:1])) \
        .filter(data__user=request.user) \
        .order_by(F("last_active")) \
        .select_related()

    active_exercises = []
    inactive_exercises = []

    for e in exercises:
        delta = timezone.now() - e.last_active

        # Round up to the nearest day
        if delta.seconds // 3600 >= 12:
            delta = delta + timedelta(days=1)

        e.delta_days = delta.days

        if e.is_active is not None:
            active_exercises.append(e)
        else:
            inactive_exercises.append(e)

    return render(request, "fitness/summary.html", {"active_exercises": active_exercises,
                                                    "inactive_exercises": inactive_exercises,
                                                    "section": SECTION,
                                                    "title": "Fitness Summary"})


@login_required
def change_active_status(request):

    exercise_id = request.POST['exercise_id']

    if request.POST['state'] == 'inactive':
        exercise = Exercise.objects.get(id=exercise_id)
        eu = ExerciseUser.objects.get(user=request.user, exercise=exercise)
        eu.delete()
        messages.add_message(request, messages.INFO, 'This exercise is no longer active')
    elif request.POST['state'] == 'active':
        exercise = Exercise.objects.get(id=exercise_id)
        eu = ExerciseUser(user=request.user, exercise=exercise)
        eu.save()
        messages.add_message(request, messages.INFO, 'This exercise is now active for you')

    return redirect('exercise_detail', exercise_id)
