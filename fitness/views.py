from django.shortcuts import render_to_response
from django.template import RequestContext

import datetime
import json

from fitness.models import Data, Exercise, Muscle, MuscleGroup

SECTION = 'Fitness'

def fitness_add(request, exercise_id):

    exercise = Exercise.objects.get(pk=exercise_id)

    if request.method == 'POST':
        for datum in json.loads(request.POST['workout-data']):
            new_data = Data(weight=datum[0], reps=datum[1], user=request.user, exercise=exercise)
            new_data.save()

    recent_data = []
    muscle_group = MuscleGroup.objects.get(id=exercise.muscle.muscle_group_id)
    muscle = exercise.muscle
    try:
        recent_data = Data.objects.filter(user=request.user, exercise__id=exercise_id).order_by('-date')[0]
    except IndexError:
        pass

    return render_to_response('fitness/add.html',
                              { 'section': SECTION,
                                'exercise': exercise,
                                'muscle_group': muscle_group,
                                'muscle': muscle,
                                'recent_data': recent_data },
                              context_instance=RequestContext(request))


def fitness_summary(request):

    exercises = Exercise.objects.all()

    recent_data = {}
    for e in exercises:
        try:
            recent_data[e.exercise] = e
            recent_data[e.exercise].date = e.data_set.order_by('-date')[0].date
            recent_data[e.exercise].delta_days = (int(datetime.datetime.now().strftime("%s")) - int(recent_data[e.exercise].date.strftime("%s")))/86400 + 1
        except IndexError:
            pass

    return render_to_response('fitness/summary.html',
                              { 'section': SECTION,
                                'recent_data': recent_data
                                },
                              context_instance=RequestContext(request))
