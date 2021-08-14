import pytest

import django
from django.apps import apps
from django.db.models import Count, Max, Min

pytestmark = pytest.mark.data_quality

django.setup()


def get_fk_model(model, query):
    """
    Helper function to get a foreign key model instance from
    a model and a foreign key field name.
    """

    fk_model = model._meta.get_field(model.field_name).remote_field.model
    fk_id = query[model.field_name]
    return fk_model.objects.get(id=fk_id)


def test_sort_order_mixin():
    """
    This test checks for three things for each model that inherits from "SortOrderMixin"

    min(sort_order) = 1
    max(sort_order) should equal the total count
    No duplicate sort_order values
    """

    models = apps.get_models()

    for model in models:

        if "SortOrderMixin" in [x.__name__ for x in model.__bases__]:

            # Use .order_by() to ignore the default ordering of the model
            field_names = model.objects.distinct(model.field_name).order_by()

            # For each model, there will be one distinct field_name per user
            for field_name in field_names:

                filter_kwargs = {field_name.field_name: getattr(field_name, field_name.field_name)}

                assert model.objects.filter(
                    **filter_kwargs
                ).aggregate(
                    Min("sort_order")
                )["sort_order__min"] == 1, f"Min(sort_order) is not 1 for {model}, {getattr(field_name, field_name.field_name)}"

                count = model.objects.filter(**filter_kwargs).count()
                assert model.objects.filter(
                    **filter_kwargs
                ).aggregate(
                    Max("sort_order")
                )["sort_order__max"] == count, f"Max(sort_order) != total count for {model}, {getattr(field_name, field_name.field_name)}"

            query = model.objects.values("sort_order", model.field_name).order_by().annotate(dcount=Count("sort_order")).filter(dcount__gt=1)
            assert len(query) == 0, f"Multiple sort_order values found for {model}, {get_fk_model(model, query[0])}"
