from django.forms import CheckboxInput, ModelForm, Select, Textarea, TextInput, ValidationError

from bookmark.models import Bookmark
from tag.models import Tag
from lib.fields import ModelCommaSeparatedChoiceField


def daily_check_test(value):
    if value == 'null':
        return False
    else:
        return True


class BookmarkForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(BookmarkForm, self).__init__(*args, **kwargs)

        self.fields['note'].required = False
        self.fields['tags'].required = False

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['tags'] = self.instance.get_tags()

    def clean_url(self):
        data = self.cleaned_data['url']
        # Verify that this url is not a dupe.  Note: exclude current url when searching.
        b = Bookmark.objects.filter(user=self.instance.user, url=data).exclude(id=self.instance.id)
        if b:
            raise ValidationError("Error: this bookmark already exists")
        return data

    def clean_daily(self):
        data = self.cleaned_data['daily']
        return data

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

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
