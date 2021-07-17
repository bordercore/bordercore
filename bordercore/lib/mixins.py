from django.apps import apps
from django.db import models, transaction
from django.db.models import F


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


class SortOrderMixin(models.Model):

    sort_order = models.IntegerField(default=1)
    note = models.TextField(blank=True, null=True)

    def delete(self):

        super().delete()

    def handle_delete(self):

        try:
            # ignore spurious nplusone warning about "Potential n+1 query detected"
            from nplusone.core import signals
            with signals.ignore(signals.lazy_load):
                filter_kwargs = {self.field_name: getattr(self, self.field_name)}
        except ModuleNotFoundError:
            # nplusone won't be installed in production
            filter_kwargs = {self.field_name: getattr(self, self.field_name)}

        self.get_queryset().filter(
            **filter_kwargs,
            sort_order__gte=self.sort_order
        ).update(
            sort_order=F("sort_order") - 1
        )

    def save(self, *args, **kwargs):

        filter_kwargs = {self.field_name: getattr(self, self.field_name)}

        # Don't do this for new objects
        if self.pk is None:
            self.get_queryset().filter(
                **filter_kwargs
            ).update(
                sort_order=F("sort_order") + 1
            )

        super().save(*args, **kwargs)

    def reorder(self, new_order):

        # Equivalent to, say, node=self.node
        filter_kwargs = {self.field_name: getattr(self, self.field_name)}

        if self.sort_order == new_order:
            return

        with transaction.atomic():
            if self.sort_order > int(new_order):
                self.get_queryset().filter(
                    **filter_kwargs,
                    sort_order__lt=self.sort_order,
                    sort_order__gte=new_order,
                ).exclude(
                    pk=self.pk
                ).update(
                    sort_order=F("sort_order") + 1,
                )
            else:
                self.get_queryset().filter(
                    **filter_kwargs,
                    sort_order__lte=new_order,
                    sort_order__gt=self.sort_order,
                ).exclude(
                    pk=self.pk,
                ).update(
                    sort_order=F("sort_order") - 1,
                )

            self.sort_order = new_order
            self.save()

    def get_queryset(self):
        model = apps.get_model(self._meta.app_label, type(self).__name__)
        return model.objects.get_queryset()

    class Meta:
        abstract = True
