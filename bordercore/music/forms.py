from django.forms import ModelForm, Select, Textarea, TextInput
from django import forms

from music.models import Song, WishList


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
            cleaned_data[field] = cleaned_data[field].strip()
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
            'title': TextInput(attrs={'class': 'form-control'}),
            'artist': TextInput(attrs={'class': 'form-control'}),
            'comment': Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'source': Select(attrs={'class': 'form-control'}),
            'track': TextInput(attrs={'class': 'form-control'}),
            'year': TextInput(attrs={'class': 'form-control'}),
            'length': TextInput(attrs={'readonly': True, 'class': 'form-control'}),
            'times_played': TextInput(attrs={'readonly': True, 'class': 'form-control'})
        }


class WishListForm(ModelForm):
    def __init__(self, *args, **kwargs):

        # In case one of our views passed in the request object (eg from get_form_kwargs()),
        #  save it and remove it from kwargs before calling super()
        if kwargs.get('request'):
            request = kwargs.pop("request")

        super(WishListForm, self).__init__(*args, **kwargs)

    class Meta:
        model = WishList
        fields = ('artist', 'song', 'album')
        widgets = {
            'artist': TextInput(attrs={'class': 'form-control'}),
            'song': TextInput(attrs={'class': 'form-control'}),
            'album': TextInput(attrs={'class': 'form-control'}),
        }
