import datetime
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Max, OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView

from .models import Data, Exercise, ExerciseUser, Workout


@method_decorator(login_required, name="dispatch")
class ExerciseDetailView(DetailView):

    model = Exercise
    slug_field = "uuid"
    slug_url_kwarg = "exercise_uuid"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        try:
            last_workout = self.object.last_workout(self.request.user)
        except IndexError:
            pass

        plot_data = self.object.get_plot_data(self.request.user)
        return {
            **context,
            **last_workout,
            "plotdata": plot_data,
            "title": f"Exercise Detail :: {self.object.name}",
            "activity_info": ExerciseUser.objects.filter(
                user=self.request.user,
                exercise__id=self.object.id
            )
        }


@login_required
def fitness_add(request, exercise_uuid):

    exercise = Exercise.objects.get(uuid=exercise_uuid)

    if request.method == "POST":

        workout = Workout(
            user=request.user,
            exercise=exercise
        )
        workout.save()
        for datum in json.loads(request.POST["workout-data"]):
            new_data = Data(
                workout=workout,
                weight=datum["weight"],
                duration=datum["duration"],
                reps=datum["reps"],
            )
            new_data.save()
        messages.add_message(request, messages.INFO, f"Added workout data for exercise <strong>{exercise}</strong>")

    return redirect("fitness:summary")


@login_required
def fitness_summary(request):

    newest = ExerciseUser.objects.filter(exercise=OuterRef("pk")) \
        .filter(user=request.user)

    exercises = Exercise.objects.annotate(
        last_active=Max("workout__data__date"),
        is_active=Subquery(newest.values("started")[:1]),
        interval=Subquery(newest.values("interval")[:1])) \
        .filter(workout__user=request.user) \
        .order_by(F("last_active")) \
        .select_related()

    active_exercises = []
    inactive_exercises = []

    for e in exercises:

        if e.last_active:

            # To determine when an exercise is overdue, convert the current datetime and the
            #  exercise's last active datetime to days since the epoch, then add one. If
            #  that exceeds the exercises's interval, it's overdue.
            if e.interval and (timezone.now() - datetime.datetime(1970, 1, 1).astimezone()).days - \
               (e.last_active - datetime.datetime(1970, 1, 1).astimezone()).days + 1 > e.interval.days:
                e.overdue = 1
            else:
                e.overdue = 0

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
                                                    "title": "Fitness Summary"})


@login_required
def change_active_status(request):

    uuid = request.POST["uuid"]
    remove = request.POST.get("remove", False)

    if remove:
        eu = ExerciseUser.objects.get(user=request.user, exercise__uuid=uuid)
        eu.delete()
    else:
        exercise = Exercise.objects.get(uuid=uuid)
        eu = ExerciseUser(user=request.user, exercise=exercise)
        eu.save()

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def edit_note(request):

    exercise_uuid = request.POST["uuid"]
    note = request.POST["note"]

    exercise = Exercise.objects.get(uuid=exercise_uuid)
    exercise.note = note
    exercise.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def get_workout_data(request):

    exercise_uuid = request.GET["uuid"]
    page_number = int(request.GET.get("page_number", 1))

    exercise = Exercise.objects.get(uuid=exercise_uuid)

    workout_data = exercise.get_plot_data(
        request.user,
        page_number=page_number
    )

    response = {
        "status": "OK",
        "workout_data": workout_data,
    }

    return JsonResponse(response)
