from django.forms import ModelForm, Textarea, ValidationError

from drill.models import Question
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class QuestionForm(ModelForm):
    def __init__(self, *args, **kwargs):

        # The request object is passed in from a view's get_form_kwargs() method
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        # Some answers might contain start with code identation required for markdown formatiing,
        #  so disable automatic whitespace stripping
        self.fields["answer"].strip = False

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial["tags"] = self.instance.get_tags()

        self.fields["tags"] = ModelCommaSeparatedChoiceField(
            request=self.request,
            required=False,
            queryset=Tag.objects.filter(user=self.request.user),
            to_field_name="name")

    def clean_tags(self):

        tags = self.cleaned_data["tags"]
        if not tags:
            self.add_error("tags", ValidationError("You must add at least one tag"))

        return tags

    class Meta:
        model = Question
        fields = ("question", "answer", "tags")
        widgets = {
            # Add "v-pre" attribute in case the question or answer happens to contain
            #  any Vue mustache tags
            "question": Textarea(attrs={"rows": 10, "class": "form-control", "v-pre": "true"}),
            "answer": Textarea(attrs={"rows": 10, "class": "form-control", "v-pre": "true"})
        }
