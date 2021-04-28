import datetime
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Max, OuterRef, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView

from fitness.models import Data, Exercise, ExerciseUser


@method_decorator(login_required, name="dispatch")
class ExerciseDetailView(DetailView):

    model = Exercise
    slug_field = "uuid"
    slug_url_kwarg = "exercise_uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uuid"] = self.object.uuid
        try:
            workout_data = Data.objects.filter(user=self.request.user, exercise__id=self.object.id).order_by("-date")[:70]
            context["recent_data"] = workout_data[0]
            context["delta_days"] = int((int(datetime.datetime.now().strftime("%s")) - int(context["recent_data"].date.strftime("%s"))) / 86400) + 1
        except IndexError:
            pass
        context["activity_info"] = ExerciseUser.objects.filter(user=self.request.user, exercise__id=self.object.id)
        context["nav"] = "fitness"
        context["title"] = f"Exercise Detail :: {self.object.name}"

        plot_data = self.get_plot_data(context, workout_data)
        context["labels"] = plot_data[0]
        context["plotdata"] = plot_data[1]

        return context

    def get_plot_data(self, context, data):

        if not data:
            return ([], [])

        # A workout is defined as all the data recorded for a specific date,
        #  regardless of time of day.

        # Find the date of the most recent workout data
        max_date = max(data, key=lambda item: item.date)

        # Find all the reps for all sets recorded on that day
        context["reps_latest_workout"] = [x.reps for x in data if x.date.strftime("%Y-%m-%d") == max_date.date.strftime("%Y-%m-%d")]

        # Create a unique collection of workout data based on date,
        #  so only one set will be extracted for each workout.

        seen = set()
        unique_workout_data = [
            x
            for x
            in data
            if x.date.strftime("Y-%m-%d") not in seen
            and not seen.add(x.date.strftime("Y-%m-%d"))
        ]
        plotdata = [x.weight for x in unique_workout_data]
        labels = [x.date.strftime("%b %d") for x in unique_workout_data]

        return (json.dumps(labels[::-1]), json.dumps(plotdata[::-1]))


@login_required
def fitness_add(request, exercise_uuid):

    exercise = Exercise.objects.get(uuid=exercise_uuid)

    if request.method == "POST":
        for datum in json.loads(request.POST["workout-data"]):
            new_data = Data(weight=datum[0], reps=datum[1], user=request.user, exercise=exercise)
            new_data.save()
        messages.add_message(request, messages.INFO, f"Added workout data for exercise <strong>{exercise}</strong>")

    return redirect("fitness:summary")


@login_required
def fitness_summary(request):

    newest = ExerciseUser.objects.filter(exercise=OuterRef("pk")) \
        .filter(user=request.user)

    exercises = Exercise.objects.annotate(
        last_active=Max("data__date", filter=Q(data__user=request.user)),
        is_active=Subquery(newest.values("started")[:1]),
        interval=Subquery(newest.values("interval")[:1])) \
        .order_by(F("last_active")) \
        .select_related()

    active_exercises = []
    inactive_exercises = []

    for e in exercises:

        if e.last_active:

            # To determine when an exercise is overdue, convert the current datetime and the
            #  exercise's last active datetime to days since the epoch, then add one. If
            #  that exceeds the exercises's interval, it's overdue.
            if e.interval and (timezone.now() - datetime.datetime(1970,1,1).astimezone()).days - \
               (e.last_active - datetime.datetime(1970,1,1).astimezone()).days + 1 > e.interval.days:
                e.overdue = True

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
                                                    "nav": "fitness",
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
