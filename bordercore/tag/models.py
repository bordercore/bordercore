"""
Models for tagging system including tags, tag-todo and tag-bookmark relations, and tag aliases.

This module defines:
- `Tag`: A label assigned to items such as bookmarks and todos.
- `TagTodo` / `TagBookmark`: Intermediate models to assign and sort tags on todos/bookmarks.
- `TagAlias`: An alternate name for a tag.
It includes logic for ensuring lowercase names, preventing name collisions, and user pinning.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Dict, Iterable, List

from django.apps import apps
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Model, Q
from django.db.models.fields.related import ForeignKey as ForeignKeyField
from django.db.models.functions import Lower
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from lib.mixins import SortOrderMixin

if TYPE_CHECKING:
    from bookmark.models import Bookmark
    from todo.models import Todo


class Tag(models.Model):
    """
    A tag is a user-defined label that can be assigned to bookmarks, todos,
    and other items. Tags can be pinned, marked as meta, and must be lowercase
    and comma-free.
    """
    name: models.TextField = models.TextField()
    is_meta: models.BooleanField = models.BooleanField(default=False)
    user: ForeignKeyField[User, Any] = models.ForeignKey(User, on_delete=models.PROTECT)
    created: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    bookmarks: models.ManyToManyField[Bookmark, int] = models.ManyToManyField(
        "bookmark.Bookmark", through="TagBookmark"
    )
    todos: models.ManyToManyField[Todo, int] = models.ManyToManyField(
        "todo.Todo", through="TagTodo"
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        unique_together = (
            ("name", "user")
        )
        constraints = [
            models.CheckConstraint(
                name="check_no_commas",
                check=~Q(name__contains=",")
            ),
            models.CheckConstraint(
                name="check_name_is_lowercase",
                check=Q(name=Lower("name"))
            )
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Validates that no TagAlias exists with the same name before saving.
        """
        if TagAlias.objects.filter(name=self.name).exists():
            raise ValidationError(f"An alias with this same name already exists: {self}")
        super().save(*args, **kwargs)

    def get_todo_counts(self) -> Iterable[Dict[str, Any]]:
        """
        Returns a QuerySet with annotation counts of all related models for this tag.

        Returns:
            A QuerySet of annotated counts.
        """
        return Tag.objects.filter(pk=self.pk) \
                          .annotate(
                              Count("blob", distinct=True),
                              Count("bookmark", distinct=True),
                              Count("album", distinct=True),
                              Count("collection", distinct=True),
                              Count("todo", distinct=True),
                              Count("question", distinct=True),
                              Count("song", distinct=True)
                          ).values()

    def pin(self) -> None:
        """
        Pin this tag to the current user's user profile using the UserTag model.
        """
        user_tag_model = apps.get_model("accounts", "UserTag")
        c = user_tag_model(userprofile=self.user.userprofile, tag=self)
        c.save()

    def unpin(self) -> None:
        """
        Unpin this tag from the current user's user profile.
        """
        user_tag_model = apps.get_model("accounts", "UserTag")
        sort_order_user_tag = user_tag_model.objects.get(userprofile=self.user.userprofile, tag=self)
        sort_order_user_tag.delete()

    @staticmethod
    def get_meta_tags(user: User) -> List[str]:
        """
        Get all distinct meta tags for the given user, using cache if available.

        Args:
            user: The user for whom to retrieve meta tags.

        Returns:
            A list of tag names marked as meta.
        """
        tags = cache.get("meta_tags")
        if not tags:
            tags = Tag.objects.filter(user=user, blob__user=user, is_meta=True).distinct("name")
            cache.set("meta_tags", tags)
        return [x.name for x in tags]


class TagTodo(SortOrderMixin):
    """
    Intermediate model linking Tags and Todos with sortable ordering.
    """
    tag: models.ForeignKey[Tag, Tag] = models.ForeignKey(Tag, on_delete=models.CASCADE)
    todo: models.ForeignKey[Todo, Todo] = models.ForeignKey("todo.Todo", on_delete=models.CASCADE)

    field_name = "tag"

    def __str__(self) -> str:
        return f"SortOrder: {self.tag}, {self.todo}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("tag", "todo")
        )


@receiver(pre_delete, sender=TagTodo)
def remove_todo(sender: type[Model], instance: TagTodo, **kwargs: Any) -> None:
    """
    Signal handler to clean up when a TagTodo is deleted.
    """
    instance.handle_delete()


class TagBookmark(SortOrderMixin):
    """
    Intermediate model linking Tags and Bookmarks with sortable ordering.
    """
    tag: models.ForeignKey[Tag, Tag] = models.ForeignKey(Tag, on_delete=models.CASCADE)
    bookmark: models.ForeignKey[Bookmark, Bookmark] = models.ForeignKey("bookmark.Bookmark", on_delete=models.CASCADE)

    field_name = "tag"

    def __str__(self) -> str:
        return f"SortOrder: {self.tag}, {self.bookmark}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("tag", "bookmark")
        )


@receiver(pre_delete, sender=TagBookmark)
def remove_bookmark(sender: type[Model], instance: TagBookmark, **kwargs: Any) -> None:
    """
    Signal handler to clean up when a TagBookmark is deleted.
    """
    instance.handle_delete()


class TagAlias(models.Model):
    """
    Represents an alternate name (alias) for a Tag. Names must be globally unique.
    """
    uuid: models.UUIDField = models.UUIDField(default=uuid.uuid4, editable=False)
    name: models.TextField = models.TextField(unique=True)
    tag: models.OneToOneField[Tag, int] = models.OneToOneField(Tag, on_delete=models.PROTECT)
    user: models.ForeignKey[User, int] = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = "Tag Aliases"
