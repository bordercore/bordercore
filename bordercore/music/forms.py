from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import (ModelChoiceField, ModelForm, Select, Textarea,
                          TextInput)
from django.forms.fields import BooleanField, CharField
from django.utils.safestring import mark_safe

from lib.fields import ModelCommaSeparatedChoiceField
from music.models import Album, Song, SongSource
from tag.models import Tag


class SongForm(ModelForm):

    sha1sum = CharField()
    album_name = CharField()
    compilation = BooleanField()

    def __init__(self, *args, **kwargs):

        # The request object is passed in from a view's SongForm() constructor
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        self.fields["source"].empty_label = None
        self.fields["track"].required = False
        self.fields["comment"].required = False
        self.fields["year"].required = False
        self.fields["tags"].required = False

        self.fields["album_name"].required = False
        self.fields["album_name"].widget.attrs["class"] = "form-control"
        self.fields["album_name"].widget.attrs["autocomplete"] = "off"

        self.fields["compilation"].required = False

        # If we're editing the metadata for an existing song,
        #  there will be no file upload and thus no sha1sum
        if "data" in kwargs and kwargs["data"]["Go"] == "Update":
            self.fields["sha1sum"].required = False

        # Use the song source stored in the user's session
        song_source = self.request.session.get("song_source", "Amazon")
        self.fields["source"].initial = SongSource.objects.get(name=song_source).id

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial["tags"] = self.instance.get_tags()

        self.fields["tags"] = ModelCommaSeparatedChoiceField(
            request=self.request,
            required=False,
            queryset=Tag.objects.filter(user=self.request.user),
            to_field_name="name")

    def clean_album_name(self):
        album_name = self.cleaned_data.get("album_name")
        artist = self.cleaned_data.get("artist")

        try:
            album = Album.objects.get(user=self.request.user,
                                      title=album_name,
                                      artist=artist)
            if album.year != self.cleaned_data.get("year"):
                listen_url = Song.get_song_url(album.song_set.all()[0])
                raise forms.ValidationError(
                    mark_safe(
                        f"Error: The <a href='{listen_url}'>same album</a> already exists but with a different year."
                    )
                )
        except ObjectDoesNotExist:
            pass

        return album_name

    def clean_year(self):
        year = self.cleaned_data.get("year")
        if not year and self.data.get("album_name"):
            raise forms.ValidationError("If you specify an album you must also specify the year")
        return year

    def clean(self):
        cleaned_data = super().clean()
        for field in ["title", "artist", "comment", "album_name"]:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].strip()

        if self.request.POST["Go"] == "Create":
            song = Song.objects.filter(
                user=self.request.user,
                title=cleaned_data["title"],
                artist=cleaned_data["artist"]
            )
            if song:
                listen_url = Song.get_song_url(song[0])
                raise ValidationError(mark_safe(f"Error: <a href='{listen_url}'>A song</a> with this title and artist already exists."))

        return cleaned_data

    source = ModelChoiceField(queryset=SongSource.objects.all(),
                              widget=forms.Select(attrs={"class": "form-control"}),
                              empty_label="Select Source")

    class Meta:
        model = Song
        fields = ("title", "artist", "track", "year", "tags", "album_name", "compilation", "comment", "source", "length", "id")
        widgets = {
            "title": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "artist": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "comment": Textarea(attrs={"rows": 2, "class": "form-control"}),
            "source": Select(),
            "track": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "year": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
        }
