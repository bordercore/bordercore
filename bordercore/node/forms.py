from django.forms import ModelForm, Textarea, TextInput

from node.models import Node


class NodeForm(ModelForm):
    def __init__(self, *args, **kwargs):

        # The request object is passed in from a view's get_form_kwargs() method
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

    class Meta:
        model = Node
        fields = ("name", "note")
        widgets = {
            "name": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "note": Textarea(attrs={"class": "form-control"})
        }
