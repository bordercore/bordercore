from django.apps import apps
from django.db.models import Count


def get_node_list(user):
    """
    Get a list of all nodes, along with their blob and bookmark counts
    """

    Node = apps.get_model("node", "Node")

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


def delete_note_from_nodes(user, note_uuid):
    """
    Delete a note from all node layouts that reference it.
    This should be called after the note itself is deleted.
    """

    Node = apps.get_model("node", "Node")

    for node in Node.objects.filter(user=user):
        changed = False
        layout = node.layout
        for i, col in enumerate(layout):
            temp_layout = [x for x in col if "uuid" not in x or x["uuid"] != str(note_uuid)]
            if layout[i] != temp_layout:
                changed = True
            layout[i] = temp_layout

        if changed:
            node.layout = layout
            node.save()
