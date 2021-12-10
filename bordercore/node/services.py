from django.db.models import Count

from node.models import Node


def get_node_list(user):
    """
    Get a list of all nodes, along with their blob and bookmark counts
    """

    nodes = Node.objects.filter(user=user) \
                        .annotate(
                            blob_count=Count("blobs")
                        ) \
                .order_by("-modified")

    bookmark_counts = {}
    for x in Node.objects.filter(user=user).annotate(bookmark_count=Count("bookmarks")):
        bookmark_counts[x.id] = x.bookmark_count

    for x in nodes:
        x.bookmark_count = bookmark_counts[x.id]

    return nodes
