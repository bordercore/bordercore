import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView

from fitness.services import get_fitness_summary

from .models import Data, Exercise, ExerciseUser, Workout


@method_decorator(login_required, name="dispatch")
class ExerciseDetailView(DetailView):

    model = Exercise
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        try:
            last_workout = self.object.last_workout(self.request.user)
        except IndexError:
            pass

        plot_data = self.object.get_plot_data()

        related_exercises = [
            {
                "uuid": x.uuid,
                "name": x.name,
                "last_active": x.last_active.strftime("%Y-%m-%d") if x.last_active else "Never"
            } for x in self.object.get_related_exercises()
        ]

        active = ExerciseUser.objects.filter(
            user=self.request.user,
            exercise__id=self.object.id
        ).first()

        if active:
            context["activity_info"] = active.activity_info()
        else:
            context["activity_info"] = {
                "schedule": [False, False, False, False, False, False, False]
            }

        return {
            **context,
            **last_workout,
            "plotdata": plot_data,
            "title": f"Exercise Detail :: {self.object.name}",
            "related_exercises": related_exercises,
        }


@login_required
def fitness_add(request, exercise_uuid):

    exercise = Exercise.objects.get(uuid=exercise_uuid)

    if request.method == "POST":

        workout = Workout(
            user=request.user,
            exercise=exercise
        )
        if "note" in request.POST:
            workout.note = request.POST["note"]
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

    exercises = get_fitness_summary(request.user)

    return render(request, "fitness/summary.html", {"active_exercises": exercises[0],
                                                    "inactive_exercises": exercises[1],
                                                    "title": "Fitness Summary"})


@login_required
def change_active_status(request):

    uuid = request.POST["uuid"]
    remove = request.POST.get("remove", "false")

    if remove == "true":
        eu = ExerciseUser.objects.get(user=request.user, exercise__uuid=uuid)
        eu.delete()
        info = {}
    else:
        exercise = Exercise.objects.get(uuid=uuid)
        eu = ExerciseUser(user=request.user, exercise=exercise, schedule=["True", "False", "False", "False", "False", "False", "False"])
        eu.save()
        info = eu.activity_info()

    return JsonResponse({"info": info, "status": "OK"}, safe=False)


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
        page_number=page_number
    )

    response = {
        "status": "OK",
        "workout_data": workout_data,
    }

    return JsonResponse(response)


@login_required
def update_schedule(request):

    uuid = request.POST["uuid"]
    schedule = request.POST["schedule"]

    # Convert each string to its corresponding Boolean value
    # "true" should become True, "false" should become False
    boolean_values = [s.lower() == "true" for s in schedule.split(",")]

    eu = ExerciseUser.objects.get(user=request.user, exercise__uuid=uuid)
    eu.schedule = boolean_values
    eu.save()

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def update_rest_period(request):

    uuid = request.POST["uuid"]
    rest_period = request.POST["rest_period"]

    eu = ExerciseUser.objects.get(user=request.user, exercise__uuid=uuid)
    eu.rest_period = rest_period
    eu.save()

    return JsonResponse({"status": "OK"}, safe=False)
