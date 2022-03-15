from elasticsearch import ConnectionTimeout

from django.conf import settings

from blob.services import get_recent_blobs as get_recent_blobs_service
from bookmark.models import Bookmark
from fitness.services import get_overdue_exercises
from metrics.models import Metric
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
