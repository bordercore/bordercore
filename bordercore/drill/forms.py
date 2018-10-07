from django.forms import ModelForm, Textarea, TextInput

from drill.models import Deck, Question
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class DeckForm(ModelForm):
    def __init__(self, *args, **kwargs):

        super(DeckForm, self).__init__(*args, **kwargs)

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = Deck
        fields = ('title', 'description')
        widgets = {
            'description': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'title': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
        }


class QuestionForm(ModelForm):
    def __init__(self, *args, **kwargs):

        super(QuestionForm, self).__init__(*args, **kwargs)

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['tags'] = self.instance.get_tags()

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = Question
        fields = ('question', 'answer')
        widgets = {
            'question': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'answer': Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }
