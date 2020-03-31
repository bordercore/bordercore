from django.forms import (ModelForm, ModelMultipleChoiceField, Textarea,
                          TextInput, ValidationError)

from feed.models import Feed


class FeedForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FeedForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Feed
        fields = ('name', 'url', 'homepage')
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'url': TextInput(attrs={'class': 'form-control'}),
            'homepage': TextInput(attrs={'class': 'form-control'}),
        }
