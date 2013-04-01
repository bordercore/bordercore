from django.forms import IntegerField, ModelForm, Textarea, TextInput, ModelChoiceField

from music.models import Song

class SongForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(SongForm, self).__init__(*args, **kwargs)
        self.fields['source'].empty_label = None

    class Meta:
        model = Song
        fields = ('title', 'artist', 'track', 'comment', 'source', 'times_played', 'id')
        widgets = {
            'title': TextInput(attrs={'class': 'input-large'}),
            'artist': TextInput(attrs={'class': 'input-large'}),
            'comment': Textarea(attrs={'rows': 2}),
            'times_played': TextInput(attrs={'readonly': True})
        }
