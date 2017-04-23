from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic.detail import DetailView

import datetime
import json

from fitness.models import Data, Exercise, ExerciseUser


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
        self.set_plot_data(context, workout_data)
        return context

    def set_plot_data(self, context, data):

        plotdata = []
        current_workout = None
        reps = []
        labels = []

        for d in data:
            day = int(d.date.strftime("%s")) / 86400
            if current_workout is not None:
                if day != int(current_workout.date.strftime("%s")) / 86400:
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


def fitness_add(request, exercise_id):

    exercise = Exercise.objects.get(pk=exercise_id)

    if request.method == 'POST':
        for datum in json.loads(request.POST['workout-data']):
            new_data = Data(weight=datum[0], reps=datum[1], user=request.user, exercise=exercise)
            new_data.save()
        messages.add_message(request, messages.INFO, 'Added workout data for exercise <strong>%s</strong>' % exercise)

    return redirect('fitness_summary')


def add_exercise_info(exercise_list, exercise):

    try:
        exercise_list[exercise.exercise] = exercise
        exercise_list[exercise.exercise].date = exercise.data_set.order_by('-date')[0].date
        exercise_list[exercise.exercise].delta_days = int((int(datetime.datetime.now().strftime("%s")) - int(exercise_list[exercise.exercise].date.strftime("%s"))) / 86400) + 1
    except IndexError:
        pass


def fitness_summary(request):

    exercises = Exercise.objects.all()

    active_exercises = {}
    inactive_exercises = {}

    for e in exercises:
        if e.exerciseuser_set.filter(user=request.user):
            add_exercise_info(active_exercises, e)
        else:
            add_exercise_info(inactive_exercises, e)

    return render(request, 'fitness/summary.html', {'active_exercises': active_exercises,
                                                    'inactive_exercises': inactive_exercises})


def change_active_status(request):

    exercise_id = request.POST['exercise_id']

    if request.POST['state'] == 'inactive':
        eu = ExerciseUser.objects.get(user=request.user, exercise=exercise_id)
        eu.delete()
        messages.add_message(request, messages.INFO, 'This exercise is no longer active')
    elif request.POST['state'] == 'active':
        e = Exercise.objects.get(id=exercise_id)
        eu = ExerciseUser(user=request.user, exercise=e)
        eu.save()
        messages.add_message(request, messages.INFO, 'This exercise is now active for you')

    return redirect('exercise_detail', exercise_id)
