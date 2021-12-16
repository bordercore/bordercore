from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from django.contrib import messages

from blob.models import Blob
from bookmark.models import Bookmark
from collection.models import Collection
from drill.models import Question
from feed.models import Feed, FeedItem
from music.models import Album, Playlist, PlaylistItem, Song, SongSource
from tag.models import Tag, TagAlias
from todo.models import Todo

from .serializers import (AlbumSerializer, BlobSerializer,
                          BlobSha1sumSerializer, BookmarkSerializer,
                          CollectionSerializer, FeedItemSerializer,
                          FeedSerializer, PlaylistItemSerializer,
                          PlaylistSerializer, QuestionSerializer,
                          SongSerializer, SongSourceSerializer,
                          TagAliasSerializer, TagSerializer, TodoSerializer)


class AlbumViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AlbumSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Album.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tags"
        )

    def perform_destroy(self, instance):
        """
        Use this DRF hook to add a message to the user.
        """
        instance.delete()
        messages.add_message(self.request, messages.INFO, "Album successfully deleted")


class BlobViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BlobSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        """
        Only the owner of the blob or the service user has access
        """
        if self.request.user.username == "service_user":
            return Blob.objects.all()
        else:
            return Blob.objects.filter(
                user=self.request.user
            ).prefetch_related(
                "blobs",
                "metadata",
                "tags"
            )

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.index_blob()

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.index_blob()


class BlobSha1sumViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BlobSha1sumSerializer
    lookup_field = "sha1sum"

    def get_queryset(self):
        """
        Only the owner of the blob or the service user has access
        """
        if self.request.user.username == "service_user":
            return Blob.objects.all()
        else:
            return Blob.objects.filter(
                user=self.request.user
            ).prefetch_related(
                "blobs",
                "metadata",
                "tags"
            )

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.index_blob()


class BookmarkViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BookmarkSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.index_bookmark()

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.index_bookmark()


class CollectionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CollectionSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Collection.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tags", "blobs"
        )


class FeedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FeedSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Feed.objects.filter(user=self.request.user)


class FeedItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FeedItemSerializer
    queryset = FeedItem.objects.filter()

    def get_queryset(self):
        return FeedItem.objects.all().select_related("feed")


class QuestionViewSet(viewsets.ModelViewSet):
    """
    Questions for drilled spaced repetition
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Question.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tags"
        )


class SongViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SongSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Song.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tags"
        )


class SongSourceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SongSourceSerializer

    def get_queryset(self):
        return SongSource.objects.all()


class PlaylistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PlaylistSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Playlist.objects.filter(user=self.request.user)


class PlaylistItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PlaylistItemSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return PlaylistItem.objects.filter(playlist__user=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)


class TagNameViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer
    lookup_field = "name"

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)


class TagAliasViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TagAliasSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return TagAlias.objects.filter(
            user=self.request.user
        ).select_related(
            "tag"
        )


class TodoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TodoSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Todo.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tags"
        )
