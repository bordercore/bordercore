#
# Reset all questions which are due for review so that they are no
#  longer due. This is useful if you fall so far behind that you
#  need a complete restart.
#

import random
import sys
from datetime import timedelta

import django
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q
from django.utils import timezone

django.setup()

from django.contrib.auth.models import User

# The new interval will be a random number from 1 to this value
MAX_NEW_INTERVAL = 52

if len(sys.argv) < 2:
    print("Error: No username provided.")
    sys.exit(1)

username = sys.argv[1]

try:
    user = User.objects.get(username=username)
except ObjectDoesNotExist:
    print(f"User does not exist: {username}")
    sys.exit(1)

Question = apps.get_model("drill", "Question")

questions = Question.objects.filter(
    user=user,
    is_disabled=False
).filter(
    Q(
        interval__lte=timezone.now() - F("last_reviewed")
    ) | Q(
        last_reviewed__isnull=True
    )
).order_by("?")

for q in questions:
    if not q.last_reviewed:
        continue
    print(f"Resetting {q.uuid}")
    past_due = timezone.now() - q.last_reviewed
    new_interval = past_due.days + random.randint(1, MAX_NEW_INTERVAL)
    q.interval = timedelta(days=new_interval)
    q.save()
