from django.forms import (CheckboxInput, JSONField, ModelForm, Textarea,
                          TextInput, URLInput, ValidationError)

from bookmark.models import Bookmark
from lib.fields import CheckboxIntegerField, ModelCommaSeparatedChoiceField
from tag.models import Tag


class DailyCheckboxInput(CheckboxInput):

    def format_value(self, value):
        """
        This insures that the widget is never rendered with a "value" attribute.
        We only care about whether it's checked or not, not its value.
        """
        return

    def value_from_datadict(self, data, files, name):
        """
        Return JavaScript booleans rather than the default Python ones. This is
        needed to avoid an error when rendering the field value after a form
        submission that results in validation errors.
        """
        return "true" if "daily" in data else "false"


class BookmarkForm(ModelForm):

    def __init__(self, *args, **kwargs):

        # The request object is passed in from a view's get_form_kwargs() method
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        self.fields["note"].required = False
        self.fields["tags"].required = False
        self.fields["importance"].required = False
        self.fields["importance"].label = "Important"

        if self.instance.id:
            # If this form has a model attached, get the tags and display them separated by commas
            self.initial["tags"] = self.instance.get_tags()
            # If the 'daily' field is not null (ie contains JSON), set the field to True. Otherwise False.
            self.initial["daily"] = self.instance.daily is not None
            # If the "importance" field is > 1 set the field to True. Otherwise False.
            self.initial["importance"] = self.instance.importance > 1
        else:
            self.initial["daily"] = False
            self.initial["importance"] = False

        self.fields["tags"] = ModelCommaSeparatedChoiceField(
            request=self.request,
            required=False,
            queryset=Tag.objects.filter(user=self.request.user),
            to_field_name="name")

    def clean_url(self):
        data = self.cleaned_data["url"]
        # Verify that this url is not a dupe.  Note: exclude current url when searching.
        b = Bookmark.objects.filter(user=self.request.user, url=data).exclude(id=self.instance.id)
        if b:
            raise ValidationError("Error: this bookmark already exists")
        return data

    class Meta:
        model = Bookmark
        fields = ("url", "name", "note", "tags", "importance", "is_pinned", "daily", "id")
        widgets = {
            "url": URLInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "name": TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
            "note": Textarea(attrs={"rows": 3, "class": "form-control"}),
            "daily": DailyCheckboxInput(),
        }
        field_classes = {
            "daily": JSONField,
            "importance": CheckboxIntegerField
        }
