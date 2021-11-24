import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from blob.models import Blob
from collection.models import Collection
from feed.models import Feed
from lib.mixins import SortOrderMixin
from tag.models import Tag


class UserProfile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    pinned_tags = models.ManyToManyField(Tag, through="SortOrderUserTag")
    pinned_notes = models.ManyToManyField(Blob, through="SortOrderUserNote")
    feeds = models.ManyToManyField(Feed, through="SortOrderUserFeed")
    pinned_drill_tags = models.ManyToManyField(Tag, through="SortOrderDrillTag", related_name="pinned_drill_tags")
    orgmode_file = models.TextField(null=True)
    google_calendar = JSONField(blank=True, null=True)
    instagram_credentials = JSONField(blank=True, null=True)
    homepage_default_collection = models.OneToOneField(Collection, related_name='default_collection', null=True, on_delete=models.PROTECT)
    sidebar_image = models.TextField(blank=True, null=True)

    THEMES = [
        ("light", "light"),
        ("dark", "dark"),
    ]

    theme = models.CharField(
        max_length=20,
        choices=THEMES,
        default="light",
    )

    def get_tags(self):
        return ", ".join([tag.name for tag in self.pinned_tags.all()])

    def __str__(self):
        return self.user.username


class SortOrderUserTag(SortOrderMixin):

    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    field_name = "userprofile"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("userprofile", "tag")
        )


@receiver(pre_delete, sender=SortOrderUserTag)
def remove_tag(sender, instance, **kwargs):
    instance.handle_delete()


class SortOrderUserNote(SortOrderMixin):

    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    note = models.ForeignKey(Blob, on_delete=models.CASCADE)

    field_name = "userprofile"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("userprofile", "note")
        )


class SortOrderUserFeed(SortOrderMixin):

    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)

    field_name = "userprofile"

    def __str__(self):
        return f"SortOrder: {self.userprofile}, {self.feed}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("userprofile", "feed")
        )


@receiver(pre_delete, sender=SortOrderUserFeed)
def remove_feed(sender, instance, **kwargs):
    instance.handle_delete()


class SortOrderDrillTag(SortOrderMixin):

    userprofile = models.ForeignKey("accounts.UserProfile", on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    field_name = "userprofile"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("userprofile", "tag")
        )


@receiver(pre_delete, sender=SortOrderDrillTag)
def remove_tag_for_drill(sender, instance, **kwargs):
    instance.handle_delete()


def pinned_tags_has_changed(initial, form):
    """
    Check if the CSV list of pinned tags has been changed. Account
    for spaces between the tags and the sort order.
    """

    initial_sorted = sorted(initial.replace(" ", "").split(","))
    form_sorted = sorted(form.replace(" ", "").split(","))

    return not set(initial_sorted) == set(form_sorted)


@receiver(pre_delete, sender=SortOrderUserNote)
def remove_note(sender, instance, **kwargs):
    instance.handle_delete()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        p = UserProfile()
        p.user = instance
        p.save()


post_save.connect(create_user_profile, sender=User)
