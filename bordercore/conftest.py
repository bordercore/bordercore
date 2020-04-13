import os

import pytest

import django

django.setup()

from django.contrib.auth.models import User  # isort:skip


@pytest.fixture(scope="function")
def user(db):
    user = User.objects.create(username="testuser")
    yield user
