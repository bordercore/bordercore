from django.forms import (CheckboxInput, ModelForm, Select, Textarea,
                          TextInput, ValidationError)

from bookmark.models import Bookmark
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


def daily_check_test(value):
    if value == 'null':
        return False
    else:
        return True


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
            'url': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'title': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'note': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'importance': Select(attrs={'class': 'form-control', 'autocomplete': 'off'}, choices=((1, 'Normal'), (5, 'High'), (10, 'Highest'))),
            'daily': CheckboxInput(check_test=daily_check_test)
        }
