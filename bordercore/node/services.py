from django.db.models import Count

from node.models import Node


def get_node_list(user):
    """
    Get a list of all nodes, along with their blob and bookmark counts
    """

    nodes = Node.objects.filter(user=user) \
                        .annotate(
                            todo_count=Count("todos")
                        ) \
                .order_by("-modified")

    return nodes
