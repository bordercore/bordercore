import pytest

from fitness.models import ExerciseUser

pytestmark = pytest.mark.django_db


def test_fitness_str(auto_login_user, fitness):

    user, _ = auto_login_user()

    assert str(fitness[0]) == "Bench Press"
    assert "Pectoralis Major" in [x.name for x in fitness[0].muscle.all()]

    assert str(ExerciseUser.objects.get(user=user, exercise=fitness[2])) == "Squats"


def test_get_overdue_exercises(auto_login_user, fitness):

    user, _ = auto_login_user()

    overdue = ExerciseUser.get_overdue_exercises(user)

    assert overdue[0]["exercise"].exercise == fitness[2]
    assert overdue[0]["lag"] == 4

    overdue = ExerciseUser.get_overdue_exercises(user, count_only=True)
    assert overdue == 1
