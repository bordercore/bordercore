from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save

from blob.models import Blob
from collection.models import Collection
from tag.models import Tag


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    rss_feeds = ArrayField(models.IntegerField(), null=True)
    favorite_tags = models.ManyToManyField(Tag, through='SortOrder')
    favorite_notes = models.ManyToManyField(Blob, through='SortOrderNote')
    todo_default_tag = models.OneToOneField(Tag, related_name='default_tag', null=True, on_delete=models.PROTECT)
    orgmode_file = models.TextField(null=True)
    google_calendar = JSONField(blank=True, null=True)
    homepage_default_collection = models.OneToOneField(Collection, related_name='default_collection', null=True, on_delete=models.PROTECT)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.favorite_tags.all()])

    def __unicode__(self):
        return u'Profile of user: %s' % self.user


class SortOrder(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    sort_order = models.IntegerField()

    def delete(self):

        # Get all tags below this one
        id_list = SortOrder.objects.filter(user_profile=self.user_profile,
                                           sort_order__gte=self.sort_order)

        # Move them up by decreasing their sort order
        SortOrder.objects.filter(id__in=id_list).update(sort_order=F('sort_order') - 1)

        super(SortOrder, self).delete()

    def save(self, *args, **kwargs):

        sorted = SortOrder.objects.filter(user_profile=self.user_profile).order_by('sort_order')
        id_list = [x.id for x in sorted]
        SortOrder.objects.filter(id__in=id_list).update(sort_order=F('sort_order') + 1)

        # A new user -> tag relationship will have sort_order = 1
        self.sort_order = 1
        super(SortOrder, self).save(*args, **kwargs)

    @staticmethod
    def reorder(user, tag_id, new_position):
        """
        Move a given tag to a new position in a sorted list
        """

        user_profile = UserProfile.objects.get(user=user)

        # Get old position
        old_position = SortOrder.objects.get(user_profile=user_profile, tag_id=tag_id)

        if old_position.sort_order != new_position:

            if old_position.sort_order > new_position:
                # Move the tag up the list
                try:
                    # All tags between the old position and the new position
                    #  need to be re-ordered by increasing their sort order

                    # Get all tags which match this criteria
                    id_list = SortOrder.objects.filter(user_profile=user_profile,
                                                       sort_order__gte=new_position,
                                                       sort_order__lte=old_position.sort_order)

                    # Update their sort order
                    SortOrder.objects.filter(id__in=id_list).update(sort_order=F('sort_order') + 1)

                    # Finally, update the sort order for the tag in question
                    SortOrder.objects.filter(user_profile=user_profile, tag_id=tag_id).update(sort_order=new_position)
                except Exception as e:
                    print("Exception: {}".format(e))
            else:
                # Move the tag down the list
                try:
                    # All tags between the old position and the new position
                    #  need to be re-ordered by decreasing their sort order

                    # Get all tags which match this criteria
                    id_list = SortOrder.objects.filter(user_profile=user_profile,
                                                       sort_order__lte=new_position,
                                                       sort_order__gte=old_position.sort_order)

                    # Update their sort order
                    SortOrder.objects.filter(id__in=id_list).update(sort_order=F('sort_order') - 1)

                    # Finally, update the sort order for the tag in question
                    SortOrder.objects.filter(user_profile=user_profile, tag_id=tag_id).update(sort_order=new_position)
                except Exception as e:
                    print("Exception: {}".format(e))

    class Meta:
        unique_together = (

            # Avoid duplicate favorite tags
            ('user_profile', 'tag'),

        )
        ordering = ('sort_order',)


class SortOrderNote(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    note = models.ForeignKey(Blob, on_delete=models.CASCADE)
    sort_order = models.IntegerField()

    def delete(self):

        # Get all notes below this one
        id_list = SortOrderNote.objects.filter(user_profile=self.user_profile,
                                               sort_order__gte=self.sort_order)

        # Move them up by decreasing their sort order
        SortOrderNote.objects.filter(id__in=id_list).update(sort_order=F('sort_order') - 1)

        super(SortOrderNote, self).delete()

    def save(self, *args, **kwargs):

        sorted = SortOrderNote.objects.filter(user_profile=self.user_profile).order_by('sort_order')
        id_list = [x.id for x in sorted]
        SortOrderNote.objects.filter(id__in=id_list).update(sort_order=F('sort_order') + 1)

        # A new user -> note relationship will have sort_order = 1
        self.sort_order = 1
        super(SortOrderNote, self).save(*args, **kwargs)

    @staticmethod
    def reorder(user, note_id, new_position):
        """
        Move a given note to a new position in a sorted list
        """

        user_profile = UserProfile.objects.get(user=user)

        # Get old position
        old_position = SortOrderNote.objects.get(user_profile=user_profile, note_id=note_id)

        if old_position.sort_order != new_position:

            if old_position.sort_order > new_position:
                # Move the note up the list
                try:
                    # All notes between the old position and the new position
                    #  need to be re-ordered by increasing their sort order

                    # Get all notes which match this criteria
                    id_list = SortOrderNote.objects.filter(user_profile=user_profile,
                                                           sort_order__gte=new_position,
                                                           sort_order__lte=old_position.sort_order)

                    # Update their sort order
                    SortOrderNote.objects.filter(id__in=id_list).update(sort_order=F('sort_order') + 1)

                    # Finally, update the sort order for the note in question
                    SortOrderNote.objects.filter(user_profile=user_profile, note_id=note_id).update(sort_order=new_position)
                except Exception as e:
                    print("Exception: {}".format(e))
            else:
                # Move the note down the list
                try:
                    # All notes between the old position and the new position
                    #  need to be re-ordered by decreasing their sort order

                    # Get all notes which match this criteria
                    id_list = SortOrderNote.objects.filter(user_profile=user_profile,
                                                           sort_order__lte=new_position,
                                                           sort_order__gte=old_position.sort_order)

                    # Update their sort order
                    SortOrderNote.objects.filter(id__in=id_list).update(sort_order=F('sort_order') - 1)

                    # Finally, update the sort order for the note in question
                    SortOrderNote.objects.filter(user_profile=user_profile, note_id=note_id).update(sort_order=new_position)
                except Exception as e:
                    print("Exception: {}".format(e))

    class Meta:
        unique_together = (

            # Avoid duplicate favorite tags
            ('user_profile', 'note'),

        )
        ordering = ('sort_order',)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        p = UserProfile()
        p.user = instance
        p.save()


post_save.connect(create_user_profile, sender=User)
