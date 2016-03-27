from django.db import models


class TimeStampedModel(models.Model):
    """ TimeStampedModel
    An abstract base class model that provides "created" and "modified" fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)
        abstract = True
