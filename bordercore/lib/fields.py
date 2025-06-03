from django.forms import IntegerField, ModelMultipleChoiceField, TextInput

from tag.models import Tag


# http://stackoverflow.com/questions/5608576/django-enter-a-list-of-values-form-error-when-rendering-a-manytomanyfield-as-a
class ModelCommaSeparatedChoiceField(ModelMultipleChoiceField):

    widget = TextInput(attrs={"class": "form-control typeahead", "autocomplete": "off"})

    def __init__(self, *args, **kwargs):

        # Allow the user to supply a custom id attribute for the form field
        tag_id = kwargs.get("id", "")
        if tag_id:
            self.widget.attrs["id"] = tag_id
            # Remove this arg to avoid an "got an unexpected keyword argument" error
            kwargs.pop("id", None)

        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

    def clean(self, value):
        if value is not None:
            value = [item.strip() for item in value.split(",") if item.strip() != ""]  # remove padding
        # Check if any of these tags are new.  The ORM won't create them for us, and in
        # fact will complain that the tag 'is not one of the available choices.'
        # These need to be explicitly created.
            for tag in value:
                newtag, created = Tag.objects.get_or_create(user=self.request.user, name=tag)
                if created:
                    newtag.save()
        return super().clean(value)


class CheckboxIntegerField(IntegerField):
    """
    This custom field lets us use a checkbox on the form, which, if checked,
    results in an integer of 1 or 10, representing importance, stored in the
    database rather than the usual boolean value.
    """
    def to_python(self, value):

        if value is True:
            return 10
        return 1
