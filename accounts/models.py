from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from tag.models import Tag

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    rss_feeds = models.TextField()
    favorite_tags = models.ManyToManyField(Tag)
    bookmarks_show_untagged_only = models.BooleanField(default=False)
    todo_default_tag = models.OneToOneField(Tag, related_name='default_tag', null=True)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.favorite_tags.all()])

    def __unicode__(self):
        return u'Profile of user: %s' % self.user


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        p = UserProfile()
        p.user = instance
        p.save()

post_save.connect(create_user_profile, sender=User)
