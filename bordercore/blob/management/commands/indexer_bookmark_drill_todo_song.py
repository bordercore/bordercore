# Re-index all bookmarks or todo tasks in Elasticsearch

from elasticsearch import Elasticsearch

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

        for album in Album.objects.all():
            self.stdout.write(album.title)
            album.index_album(es)

    def index_bookmarks_all(self):

        for b in Bookmark.objects.all():
            self.stdout.write(b.url)
            b.index_bookmark(es)

    def index_drill_all(self):

        for q in Question.objects.all():
            self.stdout.write(str(q.uuid))
            q.index_question(es)

    def index_song_all(self):

        for s in Song.objects.all():
            self.stdout.write(f"{s.artist} - {s.title}")
            s.index_song(es)

    def index_todo_all(self):

        for t in Todo.objects.all():
            self.stdout.write(t.name)
            t.index_todo(es)
