import hashlib

from django import forms
from django.core.urlresolvers import reverse_lazy
from django.forms import (ModelForm, Select, Textarea, TextInput)
from django.utils.safestring import mark_safe

from blob.models import Document
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class DocumentForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)

        self.fields['file'].required = False
        self.fields['date'].required = False
        self.fields['date'].input_formats = ['%m-%d-%Y']
        self.fields['date'].initial = ''
        self.fields['content'].required = False
        self.fields['note'].required = False
        self.fields['tags'].required = False
        self.fields['title'].required = False

        if self.instance.id:
            # If this form has a model attached, get the tags and display them separated by commas
            self.initial['tags'] = self.instance.get_tags()

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    # TODO: Should I (can I) use separate clean_<field> functions
    #  rather than one clean() function?
    def clean(self):
        cleaned_data = super(DocumentForm, self).clean()

        try:
            cleaned_data['author'] = [x.strip() for x in ''.join(cleaned_data['author']).split(',')]
        except KeyError:
            pass

        if cleaned_data.get('sha1sum', '') == '':
            cleaned_data['sha1sum'] = None

        return cleaned_data

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            hasher = hashlib.sha1()
            for chunk in file.chunks():
                hasher.update(chunk)

            # If the sha1sum changed (or didn't exist because this is a new object), check for a dupe
            if self.instance.sha1sum != hasher.hexdigest():
                existing_file = Document.objects.filter(sha1sum=hasher.hexdigest())
                if existing_file:
                    raise forms.ValidationError(mark_safe('This file <a href="{}">already exists.</a>'.format(reverse_lazy('blob_detail', kwargs={"uuid": existing_file[0].uuid}))))
            return file

    class Meta:
        model = Document
        fields = ('file', 'title', 'date', 'tags', 'content', 'note', 'importance', 'is_blog', 'is_private', 'id')
        widgets = {
            'content': Textarea(attrs={'rows': 20, 'class': 'form-control'}),
            'note': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'importance': Select(attrs={'class': 'form-control', 'autocomplete': 'off'}, choices=((1, 'Normal'), (5, 'High'), (10, 'Highest')))
        }
