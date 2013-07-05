from django.forms import ModelForm, Textarea, TextInput
from django import forms

from music.models import Song

class SongForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(SongForm, self).__init__(*args, **kwargs)
        self.fields['source'].empty_label = None
        self.fields['track'].required = False
        self.fields['comment'].required = False
        self.fields['year'].required = False

    def clean(self):
        cleaned_data = super(SongForm, self).clean()
        for field in ['title', 'artist', 'comment']:
            cleaned_data[ field ] = cleaned_data[ field ].strip()
        return cleaned_data

    def clean_year(self):
        a = self.cleaned_data.get('year')
        if not a and self.data.get('album'):
            raise forms.ValidationError(u'If you specify an album you must also specify the year')
        return a

    class Meta:
        model = Song
        fields = ('title', 'artist', 'track', 'year', 'comment', 'source', 'times_played', 'length', 'id')
        widgets = {
            'title': TextInput(attrs={'class': 'input-large'}),
            'artist': TextInput(attrs={'class': 'input-large'}),
            'comment': Textarea(attrs={'rows': 2}),
            'length': TextInput(attrs={'readonly': True}),
            'times_played': TextInput(attrs={'readonly': True})
        }
