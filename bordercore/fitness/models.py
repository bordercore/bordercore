from datetime import timedelta

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Max, Q
from django.utils import timezone


class MuscleGroup(models.Model):
    muscle_group = models.TextField(unique=True)

    def __str__(self):
        return self.muscle_group


class Muscle(models.Model):
    muscle = models.TextField(unique=True)
    muscle_group = models.ForeignKey(MuscleGroup, on_delete=models.PROTECT)

    def __str__(self):
        return self.muscle


class Exercise(models.Model):
    exercise = models.TextField(unique=True)
    muscle = models.ForeignKey(Muscle, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return self.exercise

    @property
    def note_markdown(self):
        "Returns the exercise note with markdown support."
        return markdown.markdown(self.note, extensions=[CodeHiliteExtension(guess_lang=False), "tables"])


class Data(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
    weight = models.FloatField()
    reps = models.IntegerField()

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
        return self.exercise.exercise

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
