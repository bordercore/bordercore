from bookmark.models import Bookmark
from fitness.models import ExerciseUser
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
    exercise_count = ExerciseUser.get_overdue_exercises(request.user, count_only=True)

    bookmark_untagged_count = Bookmark.objects.filter(user=request.user, tags__isnull=True).count()

    return {
        "bookmark_untagged_count": bookmark_untagged_count,
        "exercise_count": exercise_count,
        "todo_count": todo_count
    }
