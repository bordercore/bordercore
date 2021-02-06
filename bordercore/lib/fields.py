from django.forms import ModelMultipleChoiceField, TextInput

from tag.models import Tag


# http://stackoverflow.com/questions/5608576/django-enter-a-list-of-values-form-error-when-rendering-a-manytomanyfield-as-a
class ModelCommaSeparatedChoiceField(ModelMultipleChoiceField):

    widget = TextInput(attrs={'class': 'form-control typeahead', 'autocomplete': 'off'})

    def __init__(self, *args, **kwargs):

        # Allow the user to supply a custom id attribute for the form field
        id = kwargs.get('id', '')
        if id:
            self.widget.attrs['id'] = id
            # Remove this arg to avoid an "got an unexpected keyword argument" error
            kwargs.pop('id', None)

        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

    def clean(self, value):
        if value is not None:
            value = [item.strip() for item in value.split(",") if item.strip() != '']  # remove padding
        # Check if any of these tags are new.  The ORM won't create them for us, and in
        # fact will complain that the tag 'is not one of the available choices.'
        # These need to be explicitly created.
        for tag in value:
            newtag, created = Tag.objects.get_or_create(user=self.request.user, name=tag)
            if created:
                newtag.save()
        return super().clean(value)
