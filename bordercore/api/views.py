from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from blob.models import Blob
from bookmark.models import Bookmark
from collection.models import Collection
from drill.models import Question
from feed.models import Feed, FeedItem
from music.models import Album, Song, SongSource
from tag.models import Tag
from todo.models import Todo

from .serializers import (AlbumSerializer, BlobSerializer,
                          BlobSha1sumSerializer, BookmarkSerializer,
                          CollectionSerializer, FeedItemSerializer,
                          FeedSerializer, QuestionSerializer, SongSerializer,
                          SongSourceSerializer, TagSerializer, TodoSerializer,
                          UserSerializer)


class AlbumViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AlbumSerializer

    def get_queryset(self):
        return Album.objects.filter(user=self.request.user)


class BlobViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BlobSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Blob.objects.filter(user=self.request.user)

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
        return Blob.objects.filter(user=self.request.user)


class BookmarkViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BookmarkSerializer

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

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user)


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


class QuestionViewSet(viewsets.ModelViewSet):
    """
    Questions for drilled spaced repetition
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        return Question.objects.filter(user=self.request.user)


class SongViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SongSerializer

    def get_queryset(self):
        return Song.objects.filter(user=self.request.user)


class SongSourceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SongSourceSerializer

    def get_queryset(self):
        return SongSource.objects.filter(user=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)


class TodoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TodoSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.all()
