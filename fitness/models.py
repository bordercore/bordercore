from django.contrib.auth.models import User
from django.db import models


class MuscleGroup(models.Model):
    muscle_group = models.TextField(unique=True)

    def __unicode__(self):
        return self.muscle_group


class Muscle(models.Model):
    muscle = models.TextField(unique=True)
    muscle_group = models.ForeignKey(MuscleGroup)

    def __unicode__(self):
        return self.muscle


class Exercise(models.Model):
    exercise = models.TextField(unique=True)
    muscle = models.ForeignKey(Muscle)

    def __unicode__(self):
        return self.exercise

class Data(models.Model):
    user = models.ForeignKey(User)
    exercise = models.ForeignKey(Exercise)
    date = models.DateTimeField(auto_now_add=True)
    weight = models.IntegerField()
    reps = models.IntegerField()
