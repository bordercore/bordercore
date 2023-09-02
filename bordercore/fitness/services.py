import datetime
from datetime import timedelta

from django.db.models import F, Max, OuterRef, Q, Subquery
from django.utils import timezone

from fitness.models import Exercise, ExerciseUser


def get_fitness_summary(user, count_only=False):

    newest = ExerciseUser.objects.filter(
        exercise=OuterRef("pk")
    ).filter(
        user=user
    )

    exercises = Exercise.objects.annotate(
        last_active=Max(
            "workout__data__date",
            filter=Q(workout__user=user) | Q(workout__isnull=True)
        ),
        is_active=Subquery(newest.values("started")[:1]),
        frequency=Subquery(newest.values("frequency")[:1])) \
        .order_by(F("last_active"))

    if not count_only:
        exercises = exercises.prefetch_related("muscle", "muscle__muscle_group")

    active_exercises = []
    inactive_exercises = []

    for e in exercises:

        e.overdue = 0

        if e.last_active:

            # To determine when an exercise is overdue, convert the current datetime and the
            #  exercise's last active datetime to days since the epoch, then add one. If
            #  that exceeds the exercises's frequency, it's overdue.
            if e.frequency:
                delta = (timezone.now() - datetime.datetime(1970, 1, 1).astimezone()).days - \
                    (e.last_active - datetime.datetime(1970, 1, 1).astimezone()).days + 1
                # If the delta mod frequency is zero and the workout was not earlier
                #  in the day, then it's due today
                if (delta - 1) % e.frequency.days == 0 and delta != 1:
                    # Exercise is due today
                    e.overdue = 1
                elif delta > e.frequency.days + 1:
                    # Exercise is overdue
                    e.overdue = 2

            delta = timezone.now() - e.last_active

            # Round up to the nearest day
            if delta.seconds // 3600 >= 12:
                delta = delta + timedelta(days=1)

            e.delta_days = delta.days

        if e.is_active is not None:
            active_exercises.append(e)
        else:
            inactive_exercises.append(e)

    active_exercises = sorted(active_exercises, key=lambda x: x.overdue, reverse=True)
    return active_exercises, inactive_exercises


def get_overdue_exercises(user, count_only=False):

    overdue_exercises = [
        x
        for x in
        get_fitness_summary(user, count_only)[0]
        if x.overdue in (1, 2)
    ]

    if count_only:
        return len(overdue_exercises)
    else:
        return overdue_exercises
