# Associate all objects with one tag to another tag, so that the
#  second tag can be deleted. The use-case is that the second
#  tag can be re-created as an alias of the original.

import sys

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic
from django.template.defaultfilters import pluralize

from accounts.models import SortOrderDrillTag, SortOrderUserTag, UserProfile
from blob.models import Blob
from bookmark.models import Bookmark
from collection.models import Collection
from drill.models import Question
from music.models import Song
from tag.models import SortOrderTagTodo, Tag, TagBookmark
from todo.models import Todo


class Command(BaseCommand):
    help = "Migrate tag"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tag-target",
            help="The target tag to move objects to",
            required=True
        )
        parser.add_argument(
            "--tag-source",
            help="The source tag to move objects from",
            required=True
        )
        parser.add_argument(
            "--username",
            help="The username who owns the source and target tags",
            required=True
        )
        parser.add_argument(
            "--dry-run",
            help="Dry run. Take no action",
            action="store_true"
        )

    @atomic
    def handle(self, tag_target, tag_source, username, dry_run, *args, **kwargs):

        user = User.objects.get(username=username)

        try:
            tag_target = Tag.objects.get(name=tag_target, user=user)
        except ObjectDoesNotExist:
            self.stderr.write(f"Target tag does not exist: {tag_target}")
            sys.exit(1)

        try:
            tag_source = Tag.objects.get(name=tag_source, user=user)
        except ObjectDoesNotExist:
            self.stderr.write(f"Source tag does not exist: {tag_source}")
            sys.exit(1)

        # Update bookmarks
        bookmarks = Bookmark.objects.filter(tags=tag_source, user=user)
        count = bookmarks.count()
        if count > 0:
            self.stdout.write(f"Updating {count} bookmark{pluralize(count)}")

        for bookmark in bookmarks:

            s = TagBookmark.objects.get(tag=tag_source, bookmark=bookmark)
            s.delete()

            bookmark.tags.add(tag_target)
            bookmark.tags.remove(tag_source)

            if not dry_run:
                bookmark.index_bookmark()

        # Update todos
        todos = Todo.objects.filter(tags=tag_source, user=user)
        count = todos.count()
        if count > 0:
            self.stdout.write(f"Updating {count} todo{pluralize(count)}")

        for todo in todos:

            s = SortOrderTagTodo.objects.get(tag=tag_source, todo=todo)
            s.delete()

            todo.tags.add(tag_target)
            todo.tags.remove(tag_source)

        # Update blobs
        blobs = Blob.objects.filter(tags=tag_source, user=user)
        count = blobs.count()
        if count > 0:
            self.stdout.write(f"Updating {count} blob{pluralize(count)}")

        for blob in blobs[:1]:
            blob.tags.add(tag_target)
            blob.tags.remove(tag_source)

            if not dry_run:
                blob.index_blob()

        # Update collections
        collections = Collection.objects.filter(tags=tag_source, user=user)
        count = collections.count()
        if count > 0:
            self.stdout.write(f"Updating {count} collection{pluralize(count)}")

        for collection in collections:
            collection.tags.add(tag_target)
            collection.tags.remove(tag_source)

        # Update questions
        questions = Question.objects.filter(tags=tag_source, user=user)
        count = questions.count()
        if count > 0:
            self.stdout.write(f"Updating {count} question{pluralize(count)}")

        for question in questions:
            question.tags.add(tag_target)
            question.tags.remove(tag_source)

        # Update songs
        songs = Song.objects.filter(tags=tag_source, user=user)
        count = songs.count()
        if count > 0:
            self.stdout.write(f"Updating {count} song{pluralize(count)}")

        for song in songs:
            song.tags.add(tag_target)
            song.tags.remove(tag_source)

        # Update pinned tags
        profiles = UserProfile.objects.filter(pinned_tags=tag_source, user=user)
        count = profiles.count()
        if count > 0:
            self.stdout.write("Updating 1 pinned tag")

        # Obviously, there should only ever be one profile to update
        for profile in profiles:
            s = SortOrderUserTag.objects.get(tag=tag_source, userprofile=profile)
            s.delete()

            so = SortOrderUserTag(tag=tag_target, userprofile=profile)
            so.save()

            profile.pinned_tags.add(tag_target)
            profile.pinned_tags.remove(tag_source)

        # Update pinned drill tags
        profiles = UserProfile.objects.filter(pinned_drill_tags=tag_source, user=user)
        count = profiles.count()
        if count > 0:
            self.stdout.write("Updating 1 pinned drill tag")

        # Obviously, there should only ever be one profile to update
        for profile in profiles:
            s = SortOrderDrillTag.objects.get(tag=tag_source, userprofile=profile)
            s.delete()

            so = SortOrderDrillTag(tag=tag_target, userprofile=profile)
            so.save()

            profile.pinned_tags.add(tag_target)
            profile.pinned_tags.remove(tag_source)

        # Finally, delete the source tag
        tag_source.delete()

        # Since the current method has an @atomic decorator, any exception
        #  will cause a rollback. Take advantage of this by raising
        #  an exception if we're doing a dry run to negate any database
        #  changes.
        if dry_run:
            raise CommandError("Dry run requested. No action taken.")
