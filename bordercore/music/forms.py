from django import forms
from django.forms import (ModelChoiceField, ModelForm, Select, Textarea,
                          TextInput)

from lib.fields import ModelCommaSeparatedChoiceField
from music.models import Song, SongSource
from tag.models import Tag


class SongForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(SongForm, self).__init__(*args, **kwargs)
        self.fields['source'].empty_label = None
        self.fields['track'].required = False
        self.fields['comment'].required = False
        self.fields['year'].required = False
        self.fields['tags'].required = False

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['tags'] = self.instance.get_tags()

    def clean(self):
        cleaned_data = super(SongForm, self).clean()
        for field in ['title', 'artist', 'comment']:
            cleaned_data[field] = cleaned_data[field].strip()
        return cleaned_data

    def clean_year(self):
        a = self.cleaned_data.get('year')
        if not a and self.data.get('album'):
            raise forms.ValidationError(u'If you specify an album you must also specify the year')
        return a

    source = ModelChoiceField(queryset=SongSource.objects.all(),
                              widget=forms.Select(attrs={'class': 'form-control'}),
                              empty_label='Select Source')

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = Song
        fields = ('title', 'artist', 'track', 'year', 'tags', 'comment', 'source', 'length', 'id')
        widgets = {
            'title': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'artist': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'comment': Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'source': Select(),
            'track': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'year': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        }
