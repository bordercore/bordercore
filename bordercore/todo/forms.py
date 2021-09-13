from django.forms import ModelForm, Select, Textarea, TextInput

from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag
from todo.models import Todo


class TodoForm(ModelForm):
    def __init__(self, *args, **kwargs):

        # In case one of our views passed in the request object (eg from get_form_kwargs()),
        #  save it and remove it from kwargs before calling super()
        if kwargs.get("request"):
            self.request = kwargs.pop("request")

        super().__init__(*args, **kwargs)

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial["tags"] = self.instance.get_tags()
        else:
            initial_tag = self.request.session.get("current_todo_tag", None)
            self.initial["tags"] = initial_tag

        self.fields["tags"] = ModelCommaSeparatedChoiceField(
            request=self.request,
            required=False,
            queryset=Tag.objects.filter(user=self.request.user),
            to_field_name="name")

    class Meta:
        model = Todo
        fields = ("name", "priority", "note", "url")
        widgets = {
            "priority": Select(attrs={"class": "form-control"}),
            "name": TextInput(attrs={"class": "form-control", "autocomplete": "off", "autofocus": "true"}),
            "note": Textarea(attrs={"class": "form-control", "rows": 2}),
            "url": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
        }
