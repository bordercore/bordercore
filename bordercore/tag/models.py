import uuid

from django.apps import apps
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from lib.mixins import SortOrderMixin


class Tag(models.Model):
    name = models.TextField()
    is_meta = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)

    bookmarks = models.ManyToManyField("bookmark.Bookmark", through="TagBookmark")
    todos = models.ManyToManyField("todo.Todo", through="TagTodo")

    def __str__(self):
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

    def save(self, *args, **kwargs):

        if TagAlias.objects.filter(name=self.name).exists():
            raise ValidationError(f"An alias with this same name already exists: {self}")
        super().save(*args, **kwargs)

    def get_todo_counts(self):

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

    def pin(self):

        UserTag = apps.get_model("accounts", "UserTag")
        c = UserTag(userprofile=self.user.userprofile, tag=self)
        c.save()

    def unpin(self):

        UserTag = apps.get_model("accounts", "UserTag")
        sort_order_user_tag = UserTag.objects.get(userprofile=self.user.userprofile, tag=self)
        sort_order_user_tag.delete()

    @staticmethod
    def get_meta_tags(user):
        tags = cache.get('meta_tags')
        if not tags:
            tags = Tag.objects.filter(user=user, blob__user=user, is_meta=True).distinct('name')
            cache.set('meta_tags', tags)
        return [x.name for x in tags]


class TagTodo(SortOrderMixin):

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    todo = models.ForeignKey("todo.Todo", on_delete=models.CASCADE)

    field_name = "tag"

    def __str__(self):
        return f"SortOrder: {self.tag}, {self.todo}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("tag", "todo")
        )


@receiver(pre_delete, sender=TagTodo)
def remove_todo(sender, instance, **kwargs):
    instance.handle_delete()


class TagBookmark(SortOrderMixin):

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    bookmark = models.ForeignKey("bookmark.Bookmark", on_delete=models.CASCADE)

    field_name = "tag"

    def __str__(self):
        return f"SortOrder: {self.tag}, {self.bookmark}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("tag", "bookmark")
        )


@receiver(pre_delete, sender=TagBookmark)
def remove_bookmark(sender, instance, **kwargs):
    instance.handle_delete()


class TagAlias(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    tag = models.OneToOneField(Tag, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Tag Aliases"
