from django.forms import ModelForm, Textarea, TextInput

from drill.models import Question
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class QuestionForm(ModelForm):
    def __init__(self, *args, **kwargs):

        super(QuestionForm, self).__init__(*args, **kwargs)

        # Some answers might contain start with code identation required for markdown formatiing,
        #  so disable automatic whitespace stripping
        self.fields['answer'].strip = False

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
