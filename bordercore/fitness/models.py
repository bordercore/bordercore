import datetime
import json
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Max, Q
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
    description = models.TextField(blank=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def last_workout(self, user):

        workout_data = Data.objects.filter(
            user=user,
            exercise__id=self.id
        ).order_by(
            "-date"
        )[:70]

        # What's the latest date for which we have workout data?
        last_workout_date = workout_data[0].date.astimezone().strftime("%Y-%m-%d")

        # Get all workout data from that day
        recent_data = [
            x
            for x in workout_data
            if x.date.astimezone().strftime("%Y-%m-%d") == last_workout_date
        ]

        info = {
            "recent_data": recent_data,
            "latest_reps": [x.reps or 0 for x in recent_data][::-1],
            "latest_weight": [x.weight or 0 for x in recent_data][::-1],
            "latest_duration": [x.duration or 0 for x in recent_data][::-1],
            "delta_days": int((int(datetime.datetime.now().strftime("%s")) - int(recent_data[0].date.strftime("%s"))) / 86400) + 1,
            "plot_data": self.get_plot_data(user, datetime.datetime.now())
        }

        return info

    def get_plot_data(self, user, start_date, interval=timedelta(weeks=8)):

        workout_data = Data.objects.filter(
            user=user,
            exercise__id=self.id
        ).filter(
            Q(date__gte=(start_date - interval))
        ).order_by(
            "-date"
        )

        # Create a unique collection of workout data based on date,
        #  so only one set will be extracted for each workout.

        seen = set()
        unique_workout_data = [
            x
            for x
            in workout_data
            if x.date.strftime("Y-%m-%d") not in seen
            and not seen.add(x.date.strftime("Y-%m-%d"))
        ]
        if [x.weight for x in unique_workout_data if x.weight and x.weight > 0]:
            plotdata = [x.weight for x in unique_workout_data]
        elif [x.duration for x in unique_workout_data if x.duration and x.duration > 0]:
            plotdata = [x.duration for x in unique_workout_data]
        else:
            plotdata = [x.reps for x in unique_workout_data]
        labels = [x.date.strftime("%b %d") for x in unique_workout_data]

        return (json.dumps(labels[::-1]), json.dumps(plotdata[::-1]))



class Data(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
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
            max=Max("exercise__data__date")) \
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
