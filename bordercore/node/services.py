from django.db.models import Count

from node.models import Node


def get_node_list(user):
    """
    Get a list of all nodes, along with their blob and bookmark counts
    """

    nodes = Node.objects.filter(
        user=user
    ).annotate(
        todo_count=Count("todos")
    ).order_by(
        "-modified"
    )

    for node in nodes:
        node.collection_count = len([
            True
            for sublist in node.layout
            for val in sublist
            if "uuid" in val
            and val["type"] == "collection"
        ])

    return nodes
