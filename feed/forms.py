from django.forms import ModelForm, Textarea, TextInput, ValidationError, ModelMultipleChoiceField

from feed.models import Feed

class FeedForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FeedForm, self).__init__(*args, **kwargs)

#        self.fields['note'].required = False

        # If this form has a model attached, get the tags and display them separated by commas
        # if self.instance.id:
        #     self.initial['tags'] = self.instance.get_tags()

    class Meta:
        model = Feed
        fields = ('name', 'url', 'homepage')
        widgets = {
            'name': TextInput(attrs={'class': 'input-xxlarge'}),
            'url': TextInput(attrs={'class': 'input-xxlarge'}),
            'homepage': TextInput(attrs={'class': 'input-xxlarge'}),
        }
