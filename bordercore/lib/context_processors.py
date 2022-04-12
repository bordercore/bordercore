import json

from elasticsearch import ConnectionTimeout

from django.conf import settings
from django.contrib import messages
from django.utils import timezone

from blob.services import get_recent_blobs as get_recent_blobs_service
from bookmark.models import Bookmark
from fitness.services import get_overdue_exercises
from metrics.models import Metric
from search.models import RecentSearch
from todo.models import Todo


def get_counts(request):
    """
    Get counts to display as badges on the left nav bar
    """

    if not request.user.is_authenticated:
        return {}

    # Get high priority todo items
    high_priority = Todo.get_priority_value("High")
    todo_count = Todo.objects.filter(user=request.user, priority=high_priority).count()

    # Get overdue_exercises
    exercise_count = get_overdue_exercises(request.user, True)

    bookmark_untagged_count = Bookmark.objects.filter(user=request.user, tags__isnull=True).count()

    # Get failed test count
    failed_test_count = Metric.get_failed_test_count(request.user)

    return {
        "bookmark_untagged_count": bookmark_untagged_count,
        "exercise_count": exercise_count,
        "todo_count": todo_count,
        "failed_test_count": failed_test_count
    }


def get_recent_blobs(request):
    """
    """

    if not request.user.is_authenticated:
        return {}

    message = None

    try:
        recent_blobs = get_recent_blobs_service(request.user, skip_content=True)
    except (ConnectionTimeout) as e:
        message = {
            "text": str(e),
            "statusCode": e.status_code
        }
        recent_blobs = []

    return {
        "recent_blobs": {
            "blobList": recent_blobs,
            "message": message
        }
    }


def get_recent_searches(request):
    """
    """

    if not request.user.is_authenticated:
        return {}

    recent_searches = RecentSearch.objects.filter(user=request.user)[:10]

    return {
        "recent_searches": [
            {
                "id": x.id,
                "search_text": x.search_text
            }
            for x in
            recent_searches
        ]
    }


def get_overdue_tasks(request):
    """
    Return a list of todo tasks that are overdue
    """

    if not request.user.is_authenticated:
        return {}

    tasks = [
        {
            "uuid": x.uuid,
            "name": x.name,
            "tags": [x.name for x in x.tags.all()]
        }
        for x in
        Todo.objects.filter(user=request.user, due_date__lt=timezone.now())
    ]

    # Once retrieved, remove the due dates for all overdue tasks
    Todo.objects.filter(uuid__in=[x["uuid"] for x in tasks]).update(due_date=None)

    return {
        "overdue_tasks": tasks
    }


def set_constants(request):
    """
    Get counts to display as badges on the left nav bar
    """

    if not request.user.is_authenticated:
        return {}

    return {
        "MEDIA_URL_MUSIC": settings.MEDIA_URL_MUSIC,
        "IMAGES_URL": settings.IMAGES_URL,
    }


DJANGO_TO_BOOTSTRAP = {
    "debug": "info",
    "info": "info",
    "success": "success",
    "warning": "warning",
    "error": "danger"
}


def json_messages(request):

    return {
        "json_messages": json.dumps(
            [
                {
                    "body": str(x),
                    "variant": DJANGO_TO_BOOTSTRAP[x.tags],
                    "autoHide": False
                }
                for x in
                messages.get_messages(request)
            ]
        )
    }
