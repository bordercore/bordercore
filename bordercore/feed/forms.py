from django.forms import ModelForm, TextInput

from feed.models import Feed


class FeedForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Feed
        fields = ('name', 'url', 'homepage')
        widgets = {
            'name': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'url': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'homepage': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        }
