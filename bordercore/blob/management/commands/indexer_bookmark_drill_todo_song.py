# Re-index all bookmarks or todo tasks in Elasticsearch
from elasticsearch import Elasticsearch, helpers

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from todo.models import Todo  # isort:skip
from bookmark.models import Bookmark  # isort:skip
from music.models import Album, Song  # isort:skip
from drill.models import Question  # isort:skip

es = Elasticsearch(
    [settings.ELASTICSEARCH_ENDPOINT],
    timeout=120,
    verify_certs=False
)

BATCH_SIZE = 10


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


class Command(BaseCommand):
    help = "Re-index all albums, bookmarks, songs, drill questions, or todo tasks in Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            choices=["album", "bookmark", "drill", "song", "todo"],
            help="The model to index: 'album', 'bookmark', 'drill', 'song', or 'todo'",
            required=True
        )

    @atomic
    def handle(self, *args, model, **kwargs):

        if model == "album":
            self.index_albums_all()
        if model == "bookmark":
            self.index_bookmarks_all()
        elif model == "drill":
            self.index_drill_all()
        elif model == "song":
            self.index_song_all()
        elif model == "todo":
            self.index_todo_all()

    def index_albums_all(self):

        for group in chunker(Album.objects.all(), BATCH_SIZE):
            count, errors = helpers.bulk(es, [x.elasticsearch_document for x in group])
            self.stdout.write(f"Albums added: {count}")

            if errors:
                raise IOError(f"Error indexing albums: {errors}")

    def index_bookmarks_all(self):

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        for group in chunker(Bookmark.objects.all(), BATCH_SIZE):
            count, errors = helpers.bulk(es, [x.elasticsearch_document for x in group])
            self.stdout.write(f"Bookmarks added: {count}")

            if errors:
                raise IOError(f"Error indexing bookmarks: {errors}")

    def index_drill_all(self):

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        for group in chunker(Question.objects.all(), BATCH_SIZE):
            count, errors = helpers.bulk(es, [x.elasticsearch_document for x in group])
            self.stdout.write(f"Drill questions added: {count}")

    def index_song_all(self):

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        for group in chunker(Song.objects.all(), BATCH_SIZE):
            count, errors = helpers.bulk(es, [x.elasticsearch_document for x in group])
            self.stdout.write(f"Songs added: {count}")

            if errors:
                raise IOError(f"Error indexing songs: {errors}")

    def index_todo_all(self):

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        for group in chunker(Todo.objects.all(), BATCH_SIZE):
            count, errors = helpers.bulk(es, [x.elasticsearch_document for x in group])
            self.stdout.write(f"Todos added: {count}")

            if errors:
                raise IOError(f"Error indexing todos: {errors}")
