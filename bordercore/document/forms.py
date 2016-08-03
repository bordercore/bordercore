from datetime import datetime
from django.utils.timezone import utc

from django.forms import ModelForm, Textarea, TextInput

from document.models import Document
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class DocumentForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)

        self.fields['note'].required = False
        self.fields['tags'].required = False
        self.fields['sub_heading'].required = False
        self.fields['source'].required = False
        self.fields['pub_date'].required = False
        self.fields['pub_date'].input_formats = ['%m-%d-%Y']
        self.fields['url'].required = False

        if self.instance.id:
            # If this form has a model attached, get the tags and display them separated by commas
            self.initial['tags'] = self.instance.get_tags()

            self.initial['author'] = ','.join(self.initial['author'])

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    def clean(self):
        cleaned_data = super(DocumentForm, self).clean()

        try:
            cleaned_data['author'] = [x.strip() for x in ''.join(cleaned_data['author']).split(',')]
        except KeyError:
            pass

        if cleaned_data['pub_date']:
            date = cleaned_data['pub_date']

            # By default, the time portion of the date is derived from the current time
            # utcnow = datetime.utcnow().replace(tzinfo=utc)
            cleaned_data['pub_date'] = datetime(date.year, date.month, date.day, datetime.now().hour, datetime.now().minute, datetime.now().second).replace(tzinfo=utc)

        return cleaned_data

    class Meta:
        model = Document
        fields = ('title', 'author', 'source', 'pub_date', 'tags', 'sub_heading', 'content', 'note', 'url', 'id')
        widgets = {
            'content': Textarea(attrs={'rows': 20, 'class': 'form-control'}),
            'note': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'url': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'author': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'source': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'sub_heading': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
        }
