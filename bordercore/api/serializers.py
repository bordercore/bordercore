from pathlib import Path

from rest_framework import serializers

from accounts.models import User
from blob.models import Blob, MetaData
from bookmark.models import Bookmark
from collection.models import Collection
from drill.models import Question
from feed.models import Feed, FeedItem
from music.models import Album, Song, SongSource
from tag.models import Tag
from todo.models import Todo


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ["artist", "comment", "compilation", "original_release_year",
                  "title", "year"]


class BlobFileField(serializers.RelatedField):
    """
    Extract just the filename from the file path
    """
    def to_representation(self, value):
        return Path(value.name).name


class BlobMetaDataField(serializers.RelatedField):
    def to_representation(self, value):
        return {
            value.name: value.value
        }


class BlobTagsField(serializers.RelatedField):
    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        return data

class BlobSerializer(serializers.ModelSerializer):

    uuid = serializers.UUIDField()
    file = BlobFileField(read_only=True)
    metadata_set = BlobMetaDataField(many=True, read_only=True)
    tags = BlobTagsField(queryset=Tag.objects.all(), many=True)

    class Meta:
        model = Blob
        fields = ["content", "date", "file", "id", "importance",
                  "is_private", "is_note", "metadata_set", "modified", "name",
                  "note", "sha1sum", "tags", "user", "uuid"]

    # Override __init__ so that we can parse an optional "fields" searcharg
    #  to specify which fields should be returned, overriding the default set
    def __init__(self, *args, **kwargs):

        super(BlobSerializer, self).__init__(*args, **kwargs)

        fields = self.context["request"].query_params.get("fields")
        if fields:
            fields = fields.split(",")
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class BlobSha1sumSerializer(serializers.ModelSerializer):

    file = BlobFileField(read_only=True)
    metadata_set = BlobMetaDataField(many=True, read_only=True)
    tags = BlobTagsField(many=True, read_only=True)

    class Meta:
        model = Blob
        fields = ["content", "date", "documents", "file", "id", "importance",
                  "is_private", "is_note", "metadata_set", "modified",
                  "name", "note", "sha1sum", "tags", "user", "uuid"]


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ["daily", "importance", "is_pinned", "last_check",
                  "last_response_code", "note", "name", "url", "user"]


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["blob_list", "description", "is_private", "name", "tags"]


class FeedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feed
        fields = ["homepage", "last_check", "last_response_code", "name", "url"]


class FeedItemSerializer(serializers.ModelSerializer):
    feed = FeedSerializer()

    class Meta:
        model = FeedItem
        fields = ["feed", "title", "url"]


class MetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaData
        fields = ["name", "value", "blob", "user"]


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["answer", "efactor", "interval", "last_reviewed",
                  "question", "tags", "times_failed", "user"]


class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = ["album", "artist", "comment", "last_time_played", "length",
                  "original_album", "original_year", "source", "tags",
                  "times_played", "title", "track", "uuid", "year"]


class SongSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SongSource
        fields = ["description", "name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "is_meta", "name", "url", "user"]


class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ["id", "note", "tags", "name", "url", "user", "uuid"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "url", "username", "email", "is_staff"]
