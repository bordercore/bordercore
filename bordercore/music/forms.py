from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.forms import (ModelChoiceField, ModelForm, NumberInput, Select,
                          Textarea, TextInput)
from django.forms.fields import BooleanField, CharField, FileField
from django.urls import reverse
from django.utils.safestring import mark_safe

from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag

from .models import Album, Artist, Playlist, Song, SongSource


class SongForm(ModelForm):

    album_name = CharField()
    artist = CharField(widget=forms.TextInput(
        attrs={"class": "form-control"}
    ))
    compilation = BooleanField()

    def __init__(self, *args, **kwargs):

        # The request object is passed in from a view's SongForm() constructor
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        self.fields["source"].empty_label = None
        self.fields["rating"].required = False
        self.fields["track"].required = False
        self.fields["note"].required = False
        self.fields["year"].required = False
        self.fields["original_year"].required = False
        self.fields["tags"].required = False

        self.fields["album_name"].required = False
        self.fields["album_name"].widget.attrs["class"] = "form-control"
        self.fields["album_name"].widget.attrs["autocomplete"] = "off"

        self.fields["compilation"].required = False

        # Use the song source stored in the user's session
        song_source = self.request.session.get("song_source", "Amazon")
        self.fields["source"].initial = SongSource.objects.get(name=song_source).id

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial["tags"] = self.instance.get_tags()
            self.initial["artist"] = Artist.objects.get(pk=self.instance.artist.id)

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
                listen_url = reverse("music:album_detail", args=[album.uuid])
                raise forms.ValidationError(
                    mark_safe(
                        f"Error: The <a href='{listen_url}'>same album</a> already exists but with a different year."
                    )
                )
        except ObjectDoesNotExist:
            pass

        return album_name

    def clean_artist(self):
        """
        Instead of this field displaying a foreign key id, we want to
        show the artist name instead.
        """
        data = self.cleaned_data["artist"].strip()
        artist, _ = Artist.objects.get_or_create(name=data, user=self.request.user)
        return artist

    def clean_rating(self):

        rating = self.cleaned_data.get('rating')

        # An empty rating is returned as an empty string by the
        #  form. Convert it to "None" so that the corresponding
        #  field in the database is set to "NULL".
        if rating == "":
            return None
        else:
            return rating

    def clean_year(self):
        year = self.cleaned_data.get("year")
        if not year and self.data.get("album_name"):
            raise forms.ValidationError("If you specify an album you must also specify the year")
        return year

    def clean(self):
        cleaned_data = super().clean()
        for field in ["title", "note", "album_name"]:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].strip()

        return cleaned_data

    source = ModelChoiceField(queryset=SongSource.objects.all(),
                              widget=forms.Select(attrs={"class": "form-control form-select"}),
                              empty_label="Select Source")

    class Meta:
        model = Song
        fields = ("title", "artist", "track", "year", "original_year", "tags", "album_name", "compilation", "rating", "note", "source", "length", "id")
        widgets = {
            "title": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "artist": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "note": Textarea(attrs={"rows": 2, "class": "form-control"}),
            "source": Select(),
            "track": NumberInput(attrs={"class": "form-control", "autocomplete": "off", "min": "1"}),
            "year": NumberInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "original_year": NumberInput(attrs={"class": "form-control", "autocomplete": "off"}),
        }


class PlaylistForm(ModelForm):

    name = CharField()

    def __init__(self, *args, **kwargs):

        # The request object is passed in from a view's PlaylistForm() constructor
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Playlist
        fields = ("name", "note", "size", "type")
        widgets = {
            "name": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "note": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "size": NumberInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "type": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
        }


class AlbumForm(ModelForm):

    artist = CharField(widget=forms.TextInput(
        attrs={"class": "form-control"}
    ))
    cover_image = FileField()

    def __init__(self, *args, **kwargs):

        # The request object is passed in from a view's PlaylistForm() constructor
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        self.fields["cover_image"].required = False

        if self.instance.id:
            self.initial["tags"] = self.instance.get_tags()
            self.initial["artist"] = Artist.objects.get(pk=self.instance.artist.id)

        self.fields["tags"] = ModelCommaSeparatedChoiceField(
            request=self.request,
            required=False,
            queryset=Tag.objects.filter(user=self.request.user),
            to_field_name="name")

    def clean_artist(self):
        """
        Instead of this field displaying a foreign key id, we want to
        show the artist name instead.
        """
        data = self.cleaned_data["artist"]
        artist, _ = Artist.objects.get_or_create(name=data, user=self.request.user)
        return artist

    class Meta:
        model = Album
        fields = ("title", "artist", "year", "note")
        widgets = {
            "title": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "year": NumberInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "note": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
        }
