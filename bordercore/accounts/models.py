import uuid

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from blob.models import Blob
from collection.models import Collection
from lib.mixins import SortOrderMixin
from tag.models import Tag


class UserProfile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    rss_feeds = ArrayField(models.IntegerField(), null=True)
    favorite_tags = models.ManyToManyField(Tag, through="SortOrderUserTag")
    favorite_notes = models.ManyToManyField(Blob, through="SortOrderUserNote")
    todo_default_tag = models.OneToOneField(Tag, related_name='default_tag', null=True, on_delete=models.PROTECT)
    orgmode_file = models.TextField(null=True)
    google_calendar = JSONField(blank=True, null=True)
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
        return ", ".join([tag.name for tag in self.favorite_tags.all()])

    def __unicode__(self):
        return u'Profile of user: %s' % self.user


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


@receiver(pre_delete, sender=SortOrderUserNote)
def remove_note(sender, instance, **kwargs):
    instance.handle_delete()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        p = UserProfile()
        p.user = instance
        p.save()


post_save.connect(create_user_profile, sender=User)
