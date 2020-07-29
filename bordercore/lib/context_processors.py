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

    return {
        "todo_count": todo_count
    }
