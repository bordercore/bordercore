from django.contrib.postgres.forms import JSONField
from django.forms import (CheckboxInput, ModelForm, Select, Textarea,
                          TextInput, URLInput, ValidationError)

from bookmark.models import Bookmark
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


def daily_check_test(value):
    """
    Interpret a null value from the database as False, and leave the checkbox unchecked.
    Otherwise it's true and checked.
    """
    if value == 'null' or value == 'false':
        return False
    else:
        return True


class DailyCheckboxInput(CheckboxInput):

    def format_value(self, value):
        """
        This insures that the widget is never rendered with a "value" attribute.
        We only care about whether it's checked or not, not its value.
        """
        return


class CheckboxJSONField(JSONField):

    def bound_data(self, data, initial):
        """
        Return the value that should be shown for this field on render of a
        bound form, given the submitted POST data for the field and the initial
        data, if any.
        We override this to prevent the default JSONField from throwing an error
        when trying to decode a boolean value (from the checkbox) as valid JSON.
        """
        if self.disabled:
            return initial
        return data


class BookmarkForm(ModelForm):

    def __init__(self, *args, **kwargs):

        # The request object is passed in from  a view's get_form_kwargs() method
        self.request = kwargs.pop('request', None)

        super().__init__(*args, **kwargs)

        self.fields['note'].required = False
        self.fields['tags'].required = False

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['tags'] = self.instance.get_tags()

        self.fields['tags'] = ModelCommaSeparatedChoiceField(
            request=self.request,
            required=False,
            queryset=Tag.objects.filter(user=self.request.user),
            to_field_name='name')

    def clean_url(self):
        data = self.cleaned_data['url']
        # Verify that this url is not a dupe.  Note: exclude current url when searching.
        b = Bookmark.objects.filter(user=self.request.user, url=data).exclude(id=self.instance.id)
        if b:
            raise ValidationError("Error: this bookmark already exists")
        return data

    class Meta:
        model = Bookmark
        fields = ('url', 'title', 'note', 'tags', 'importance', 'is_pinned', 'daily', 'id')
        widgets = {
            'url': URLInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'title': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'note': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'importance': Select(attrs={'class': 'form-control', 'autocomplete': 'off'}, choices=((1, 'Normal'), (5, 'High'), (10, 'Highest'))),
            'daily': DailyCheckboxInput(check_test=daily_check_test)
        }
        field_classes = {
            'daily': CheckboxJSONField,
        }
