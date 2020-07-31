from django.contrib import admin

from fitness.models import Data, Exercise, ExerciseUser, Muscle, MuscleGroup

admin.site.register(Data)
admin.site.register(Exercise)
admin.site.register(ExerciseUser)
admin.site.register(Muscle)
admin.site.register(MuscleGroup)
