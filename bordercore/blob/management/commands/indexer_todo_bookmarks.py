# Re-index all bookmarks or todo tasks in Elasticsearch

from elasticsearch import Elasticsearch

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from todo.models import Todo  # isort:skip
from bookmark.models import Bookmark  # isort:skip


es = Elasticsearch(
    [settings.ELASTICSEARCH_ENDPOINT],
    timeout=120,
    verify_certs=False
)


class Command(BaseCommand):
    help = "Re-index all bookmarks or todo tasks in Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            choices=["bookmark", "todo"],
            help="The model to index: 'bookmark' or 'todo'",
            required=True
        )

    @atomic
    def handle(self, *args, model, **kwargs):

        if model == "bookmark":
            self.index_bookmarks_all()
        elif model == "todo":
            self.index_todo_all()

    def index_bookmarks_all(self):

        for b in Bookmark.objects.all():
            self.stdout.write(b.url)
            b.index_bookmark(es)

    def index_todo_all(self):

        for t in Todo.objects.all():
            self.stdout.write(t.task)
            t.index_todo(es)
