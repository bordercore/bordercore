from datetime import datetime
from django.utils.timezone import utc

from django.forms import ModelForm, Textarea, TextInput

from blog.models import Post, Tag
from lib.fields import ModelCommaSeparatedChoiceField


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

        # By default, the time portion of the date is derived from the current time
        # utcnow = datetime.utcnow().replace(tzinfo=utc)
        cleaned_data['date'] = datetime(date.year, date.month, date.day, datetime.now().hour, datetime.now().minute, datetime.now().second).replace(tzinfo=utc)
        return cleaned_data

    class Meta:
        model = Post
        fields = ('title', 'date', 'post', 'tags', 'id')
        widgets = {
            'post': Textarea(attrs={'rows': 20, 'class': 'form-control'}),
            'title': TextInput(attrs={'class': 'form-control'}),
        }
