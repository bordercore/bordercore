from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from lib.mixins import SortOrderMixin


class Tag(models.Model):
    name = models.TextField(unique=True)
    is_meta = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    bookmarks = models.ManyToManyField("bookmark.Bookmark", through="SortOrderTagBookmark")
    todos = models.ManyToManyField("todo.Todo", through="SortOrderTagTodo")

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    @staticmethod
    def get_meta_tags(user):
        tags = cache.get('meta_tags')
        if not tags:
            tags = Tag.objects.filter(blob__user=user, is_meta=True)
            cache.set('meta_tags', tags)
        return [x.name for x in tags]


class SortOrderTagTodo(SortOrderMixin):

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    todo = models.ForeignKey("todo.Todo", on_delete=models.CASCADE)

    field_name = "tag"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("tag", "todo")
        )


@receiver(pre_delete, sender=SortOrderTagTodo)
def remove_todo(sender, instance, **kwargs):
    instance.handle_delete()


class SortOrderTagBookmark(SortOrderMixin):

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    bookmark = models.ForeignKey("bookmark.Bookmark", on_delete=models.CASCADE)

    field_name = "tag"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("tag", "bookmark")
        )


@receiver(pre_delete, sender=SortOrderTagBookmark)
def remove_bookmark(sender, instance, **kwargs):
    instance.handle_delete()


class TagAlias(models.Model):
    name = models.TextField(unique=True)
    tag = models.OneToOneField(Tag, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = "Tag Aliases"

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name
