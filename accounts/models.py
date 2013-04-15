from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    rss_feeds = models.TextField()

    def __unicode__(self):
        return u'Profile of user: %s' % self.user


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        p = UserProfile()
        p.user = instance
        p.save()

post_save.connect(create_user_profile, sender=User)
