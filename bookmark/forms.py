from django.forms import ModelForm, Textarea, TextInput, ValidationError, ModelMultipleChoiceField

from bookmark.models import Bookmark
from blog.models import Tag

# http://stackoverflow.com/questions/5608576/django-enter-a-list-of-values-form-error-when-rendering-a-manytomanyfield-as-a
class ModelCommaSeparatedChoiceField(ModelMultipleChoiceField):
    widget = TextInput

    def clean(self, value):
        if value is not None:
            value = [item.strip() for item in value.split(",") if item.strip() != ''] # remove padding
        return super(ModelCommaSeparatedChoiceField, self).clean(value)

class BookmarkForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(BookmarkForm, self).__init__(*args, **kwargs)

        self.fields['note'].required = False
        self.fields['tags'].required = False

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['tags'] = self.instance.get_tags()

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = Bookmark
        fields = ('url', 'title', 'note', 'tags', 'id')
        widgets = {
            'url': TextInput(attrs={'class': 'input-xxlarge'}),
            'title': TextInput(attrs={'class': 'input-xxlarge'}),
            'note': Textarea(attrs={'rows': 3}),
            'tags': TextInput()
        }
