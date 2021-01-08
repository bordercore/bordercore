import datetime
import hashlib
import re

from django import forms
from django.forms import (ModelForm, Select, Textarea, TextInput,
                          ValidationError)
from django.forms.fields import CharField, IntegerField
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

from blob.models import ILLEGAL_FILENAMES, Blob
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class BlobForm(ModelForm):

    def __init__(self, *args, **kwargs):

        # The request object is passed in from a view's SongForm() constructor
        self.request = kwargs.pop("request", None)

        super(BlobForm, self).__init__(*args, **kwargs)

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

            self.initial['date'] = self.instance.get_cleaned_date(self.instance.date)
        else:
            self.fields['filename'].disabled = True
            self.initial['date'] = datetime.date.today().strftime("%Y-%m-%dT00:00")

        self.fields['tags'] = ModelCommaSeparatedChoiceField(
            request=self.request,
            required=False,
            queryset=Tag.objects.filter(user=self.request.user),
            to_field_name='name')

    filename = CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    file_modified = IntegerField(required=False, widget=forms.HiddenInput())

    # TODO: Should I (can I) use separate clean_<field> functions
    #  rather than one clean() function?
    def clean(self):
        cleaned_data = super(BlobForm, self).clean()

        try:
            cleaned_data['author'] = [x.strip() for x in ''.join(cleaned_data['author']).split(',')]
        except KeyError:
            pass

        if cleaned_data.get('sha1sum', '') == '':
            cleaned_data['sha1sum'] = None

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

    def clean_file(self):
        file = self.cleaned_data.get("file")

        # This insures that we only check for a dupe if the user
        #  added a file via file upload rather than simply edit the
        #  metadata for a file. Without this check the actual file
        #  can't be found to compute the sha1sum.
        if self.files.get("file", None):

            hasher = hashlib.sha1()
            for chunk in file.chunks():
                hasher.update(chunk)

            # If the sha1sum changed (or didn't exist because this is a new object), check for a dupe
            if self.instance.sha1sum != hasher.hexdigest():
                existing_file = Blob.objects.filter(sha1sum=hasher.hexdigest())
                if existing_file:
                    url = reverse_lazy("blob:detail", kwargs={"uuid": existing_file[0].uuid})
                    raise forms.ValidationError(mark_safe(f'This file <a href="{url}">already exists.</a>'))

        return file

    def clean_date(self):
        date = self.cleaned_data.get("date")

        regex1 = r"^\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d$"
        regex2 = r"^\d\d\d\d-\d\d-\d\d$"
        regex3 = r"^\d\d\d\d-\d\d$"
        regex4 = r"^\d\d\d\d$"
        regex5 = r"^\[(\d\d\d\d-\d\d) TO \d\d\d\d-\d\d\]$"
        regex6 = r"^$"  # Empty dates are fine

        if not re.match("|".join([regex1, regex2, regex3, regex4, regex5, regex6]), date):
            raise forms.ValidationError("Error: invalid date format")

        return date

    class Meta:
        model = Blob
        fields = ('file', 'title', 'filename', 'file_modified', 'date', 'tags', 'content', 'note', 'importance', 'is_note', 'is_private', 'id')
        widgets = {
            'content': Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'note': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'importance': Select(attrs={'class': 'form-control', 'autocomplete': 'off'}, choices=((1, 'Normal'), (5, 'High'), (10, 'Highest')))
        }
