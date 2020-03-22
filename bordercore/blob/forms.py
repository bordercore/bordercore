import hashlib
import os

from blob.models import ILLEGAL_FILENAMES, Document
from django import forms
from django.conf import settings
from django.forms import (ModelForm, Select, Textarea, TextInput,
                          ValidationError)
from django.forms.fields import CharField, IntegerField
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class DocumentForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.fields['file'].required = False
        self.fields['file'].label = "File"
        self.fields['date'].required = False
        self.fields['date'].input_formats = ['%m-%d-%Y']
        self.fields['date'].initial = ''
        self.fields['content'].required = False
        self.fields['note'].required = False
        self.fields['tags'].required = False
        self.fields['title'].required = False

        if self.instance.id:
            self.fields['filename'].initial = self.instance.file

            # If this form has a model attached, get the tags and display them separated by commas
            self.initial['tags'] = self.instance.get_tags()
        else:
            self.fields['filename'].disabled = True

    filename = CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    file_modified = IntegerField(required=False, widget=forms.HiddenInput())

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

        # old_filename = str(self.instance.file)
        # if (cleaned_data.get('filename', '') != os.path.basename(old_filename)):
        #     new_file_path = '{}/{}/{}'.format(settings.MEDIA_ROOT, os.path.dirname(old_filename), cleaned_data['filename'])
        #     if os.path.isfile(new_file_path):
        #         self.add_error("file", ValidationError("Rename failed: file exists"))

        return cleaned_data

    def clean_filename(self):

        filename = str(self.cleaned_data.get("filename"))

        if filename in ILLEGAL_FILENAMES:
            self.add_error("filename", ValidationError(f"Error: Illegal filename: {filename}"))

        return filename

    def clean_file_modified(self):
        """
        The "file modified" timestamp is set by Javacript in milliseconds.
        We don't need that much precision, so convert to seconds.
        """
        data = self.cleaned_data.get("file_modified")
        if data:
            return int(data / 1000)
        else:
            return data

     # def clean_file(self):
    #     file = self.cleaned_data.get("file")
    #     if file:
    #         hasher = hashlib.sha1()
    #         for chunk in file.chunks():
    #             hasher.update(chunk)

    #         # If the sha1sum changed (or didn't exist because this is a new object), check for a dupe
    #         if self.instance.sha1sum != hasher.hexdigest():
    #             existing_file = Document.objects.filter(sha1sum=hasher.hexdigest())
    #             if existing_file:
    #                 raise forms.ValidationError(mark_safe('This file <a href="{}">already exists.</a>'.format(reverse_lazy('blob_detail', kwargs={"uuid": existing_file[0].uuid}))))
    #         return file

    class Meta:
        model = Document
        # fields = ('file', 'title', 'filename', 'file_modified', 'date', 'tags', 'content', 'note', 'importance', 'is_note', 'is_private', 'id')
        fields = ('file', 'title', 'filename', 'file_modified', 'date', 'tags', 'content', 'note', 'importance', 'is_note', 'is_private', 'id')
        widgets = {
            'content': Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'note': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'importance': Select(attrs={'class': 'form-control', 'autocomplete': 'off'}, choices=((1, 'Normal'), (5, 'High'), (10, 'Highest')))
        }
