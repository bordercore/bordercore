import datetime
import hashlib
import re

from django import forms
from django.forms import (CheckboxInput, ModelForm, Textarea, TextInput,
                          ValidationError)
from django.forms.fields import CharField, IntegerField
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

from blob.models import ILLEGAL_FILENAMES, Blob
from lib.fields import CheckboxIntegerField, ModelCommaSeparatedChoiceField
from lib.time_utils import get_javascript_date
from tag.models import Tag


class BlobForm(ModelForm):

    def __init__(self, *args, **kwargs):

        # The request object is passed in from a view's SongForm() constructor
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        self.fields["file"].required = False
        self.fields["file"].label = "File"
        self.fields["date"].required = False
        self.fields["date"].input_formats = ["%m-%d-%Y"]
        self.fields["date"].initial = ""
        self.fields["content"].required = False
        self.fields["note"].required = False
        self.fields["tags"].required = False
        self.fields["name"].required = False
        self.fields["importance"].required = False

        if self.instance.id:
            self.fields["filename"].initial = self.instance.file

            # If this form has a model attached, get the tags and display them separated by commas
            self.initial["tags"] = self.instance.get_tags()

            if self.instance.date:
                self.initial["date"] = get_javascript_date(self.instance.date)
        else:
            self.initial["date"] = datetime.date.today().strftime("%Y-%m-%dT00:00")

        self.fields["tags"] = ModelCommaSeparatedChoiceField(
            request=self.request,
            required=False,
            queryset=Tag.objects.filter(user=self.request.user),
            to_field_name="name")

    filename = CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    file_modified = IntegerField(required=False, widget=forms.HiddenInput())

    def clean_filename(self):
        filename = str(self.cleaned_data.get("filename"))
        if filename in ILLEGAL_FILENAMES:
            self.add_error("filename", ValidationError(f"Error: Illegal filename: {filename}"))

        return filename

    def clean_file(self):
        file = self.cleaned_data.get("file")

        # This insures that we only check for a dupe if the user
        #  added a file via file upload rather than simply edit the
        #  metadata for a file. Without this check the actual file
        #  can't be found to compute the sha1sum.
        if "file" in self.files:
            hasher = hashlib.sha1()
            for chunk in file.chunks():
                hasher.update(chunk)

            # If the sha1sum changed (or didn't exist because this is a new object), check for a dupe
            if self.instance.sha1sum != hasher.hexdigest():
                existing_file = Blob.objects.filter(sha1sum=hasher.hexdigest())
                if existing_file:
                    url = reverse_lazy("blob:detail", kwargs={"uuid": existing_file[0].uuid})
                    raise forms.ValidationError(mark_safe(f"Error: This file <a href='{url}'>already exists.</a>"))

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
        fields = ("file", "name", "filename", "file_modified", "date", "tags", "content", "note", "importance", "is_note", "id", "math_support")
        widgets = {
            "content": Textarea(attrs={"rows": 5, "class": "form-control"}),
            "note": Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    ":class": "{'drag-over': isDragOver.note}",
                    "@dragover.prevent": "isDragOver.note = true",
                    "@dragleave.prevent": "isDragOver.note = false",
                    "@drop": "isDragOver.note = false",
                    "@drop.prevent": "handleLinkDrop"
                }
            ),
            "name": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "importance": CheckboxInput(),
        }
        field_classes = {
            "importance": CheckboxIntegerField
        }
