from datetime import datetime
from django.utils.timezone import utc

from django.forms import ModelForm, Textarea, TextInput, ModelMultipleChoiceField

from document.models import Document
from tag.models import Tag


# http://stackoverflow.com/questions/5608576/django-enter-a-list-of-values-form-error-when-rendering-a-manytomanyfield-as-a
class ModelCommaSeparatedChoiceField(ModelMultipleChoiceField):
    widget = TextInput(attrs={'class': 'form-control'})

    def clean(self, value):
        if value is not None:
            value = [item.strip().lower() for item in value.split(",") if item.strip() != '']  # remove padding and force lowercase
        # Check if any of these tags are new.  The ORM won't create them for us, and in
        # fact will complain that the tag 'is not one of the available choices.'
        # These need to be explicitly created.
        for tag in value:
            newtag, created = Tag.objects.get_or_create(name=tag)
            if created:
                newtag.save()
        return super(ModelCommaSeparatedChoiceField, self).clean(value)


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

        # else:
        #     # For new documents, set the default date to now
        #     self.initial['pub_date'] = datetime.now()

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    def clean(self):
        cleaned_data = super(DocumentForm, self).clean()

        cleaned_data['author'] = [x.strip() for x in ''.join( cleaned_data['author'] ).split(',') ]

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
