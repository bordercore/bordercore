import datetime
import json
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Max, OuterRef, Q, Subquery
from django.utils import timezone


class MuscleGroup(models.Model):
    name = models.TextField(unique=True)

    def __str__(self):
        return self.name


class Muscle(models.Model):
    name = models.TextField(unique=True)
    muscle_group = models.ForeignKey(MuscleGroup, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Exercise(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    muscle = models.ForeignKey(Muscle, on_delete=models.PROTECT)
    muscle_new = models.ManyToManyField(Muscle, through="SortOrderExerciseMuscle", related_name="muscle")
    description = models.TextField(blank=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def last_workout(self, user):

        workout = Workout.objects.filter(
            user=user,
            exercise__id=self.id
        ).order_by(
            "-date"
        ).first()

        recent_data = workout.data_set.all()

        info = {
            "recent_data": recent_data,
            "latest_reps": [x.reps or 0 for x in recent_data][::-1],
            "latest_weight": [x.weight or 0 for x in recent_data][::-1],
            "latest_duration": [x.duration or 0 for x in recent_data][::-1],
            "delta_days": int((int(datetime.datetime.now().strftime("%s")) - int(recent_data[0].date.strftime("%s"))) / 86400) + 1,
        }

        return info

    def get_plot_data(self, user, start_date, count=8, interval=timedelta(weeks=8)):

        workout_data = Data.objects.filter(workout=OuterRef("pk"), user=user)

        raw_data = Workout.objects.filter(exercise__id=self.id) \
                                  .filter(date__lt=start_date) \
                                  .annotate(reps=Subquery(workout_data.values("reps")[:1])) \
                                  .annotate(weight=Subquery(workout_data.values("weight")[:1])) \
                                  .annotate(duration=Subquery(workout_data.values("duration")[:1])) \
                                  .order_by("-date")[:count]

        if [x.weight for x in raw_data if x.weight and x.weight > 0]:
            plotdata = [x.weight for x in raw_data]
        elif [x.duration for x in raw_data if x.duration and x.duration > 0]:
            plotdata = [x.duration for x in raw_data]
        else:
            plotdata = [x.reps for x in raw_data]
        labels = [x.date.strftime("%b %d") for x in raw_data]

        return (
            json.dumps(labels[::-1]),
            json.dumps(plotdata[::-1]),
            list(raw_data)[-1].date.strftime("%Y-%m-%d"))


class SortOrderExerciseMuscle(models.Model):

    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    muscle = models.ForeignKey(Muscle, on_delete=models.CASCADE)
    note = models.TextField(blank=True, null=True)

    WEIGHTS = [
        ("primary", "primary"),
        ("secondary", "secondary"),
    ]

    theme = models.CharField(
        max_length=20,
        choices=WEIGHTS,
        default="primary",
    )

    def __str__(self):
        return f"SortOrderExerciseMuscle: {self.exercise}, {self.muscle}"

    class Meta:
        unique_together = (
            ("exercise", "muscle")
        )


class Workout(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)


class Data(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    workout = models.ForeignKey(Workout, on_delete=models.PROTECT, null=True)
    date = models.DateTimeField(auto_now_add=True)
    weight = models.FloatField(blank=True, null=True)
    reps = models.IntegerField()
    duration = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Data"


class ExerciseUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    started = models.DateTimeField(auto_now_add=True)
    interval = models.DurationField(default=timedelta(days=7), blank=False, null=False)

    class Meta:
        unique_together = ("user", "exercise")

    def __str__(self):
        return self.exercise.name

    @staticmethod
    def get_overdue_exercises(user, count_only=False):

        exercises = ExerciseUser.objects.annotate(
            max=Max("exercise__workout__data__date")) \
            .filter(Q(interval__lt=(timezone.now() - F("max")) + timedelta(days=1))) \
            .filter(user=user) \
            .order_by(F("max"))

        # Avoid an unnecessary join if we only want the count
        if not count_only:
            exercises = exercises.select_related("exercise")

        overdue_exercises = []

        for exercise in exercises:
            delta = timezone.now() - exercise.max

            # Round up to the nearest day
            if delta.total_seconds() // 3600 >= 12:
                delta = delta + timedelta(days=1)

                overdue_exercises.append(
                    {
                        "exercise": exercise,
                        "lag": delta.days
                    }
                )

        if count_only:
            return len(overdue_exercises)
        else:
            return overdue_exercises
