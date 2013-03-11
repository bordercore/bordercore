from datetime import datetime

from django.forms import ModelForm, Textarea, TextInput, ModelMultipleChoiceField

from blog.models import Post, Tag

# http://stackoverflow.com/questions/5608576/django-enter-a-list-of-values-form-error-when-rendering-a-manytomanyfield-as-a
class ModelCommaSeparatedChoiceField(ModelMultipleChoiceField):
    widget = TextInput

    def clean(self, value):
        if value is not None:
            value = [item.strip() for item in value.split(",") if item.strip() != ''] # remove padding
        return super(ModelCommaSeparatedChoiceField, self).clean(value)

class BlogForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(BlogForm, self).__init__(*args, **kwargs)

        self.fields['title'].required = False
        self.fields['tags'].required = False
        self.fields['date'].input_formats = ['%m-%d-%Y']

        if self.instance.id:
            # If this form has a model attached, get the tags and display them separated by commas
            self.initial['tags'] = self.instance.get_tags()
        else:
            # For new posts, set the default date to now
            self.initial['date'] = datetime.now()

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    def clean(self):
        cleaned_data = super(BlogForm, self).clean()
        date = cleaned_data['date']

        print "calling clean"

        # By default, the time portion of the date is derived from the current time
        cleaned_data['date'] = datetime(date.year, date.month, date.day, datetime.now().hour, datetime.now().minute, datetime.now().second)
        return cleaned_data

    class Meta:
        model = Post
        fields = ('title', 'date', 'post', 'tags', 'id')
        widgets = {
            'post': Textarea(attrs={'rows': 20, 'class': 'input-xxlarge'}),
            'title': TextInput(attrs={'class': 'input-xxlarge'}),
            'tags': TextInput()
        }
