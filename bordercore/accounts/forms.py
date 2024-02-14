from django.forms import (ModelChoiceField, ModelForm, Select, Textarea,
                          TextInput)

from accounts.models import UserProfile
from collection.models import Collection


class UserProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):

        # The request object is passed in from UserProfileUpdateView.get_form_kwargs()
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        self.fields["drill_intervals"].widget.attrs["class"] = "form-control"
        self.fields["nytimes_api_key"].label = "NYTimes API key"
        self.fields["nytimes_api_key"].required = False

        collections_list = Collection.objects.filter(user=self.request.user).exclude(name="")
        if collections_list:
            self.fields["homepage_default_collection"] = ModelChoiceField(
                empty_label="Select Collection",
                label="Default collection",
                queryset=collections_list,
                required=False,
                to_field_name="id"
            )
            self.fields["homepage_image_collection"] = ModelChoiceField(
                empty_label="All Images",
                label="Image collection",
                queryset=collections_list,
                required=False,
                to_field_name="id"
            )
            self.fields["homepage_default_collection"].widget.attrs["class"] = "form-control form-select"
            self.fields["homepage_image_collection"].widget.attrs["class"] = "form-control form-select"
        else:
            # If the user doesn't have any collections, remove the field
            self.fields.pop("homepage_default_collection")

    class Meta:
        model = UserProfile
        fields = (
            "theme",
            "background_image",
            "sidebar_image",
            "homepage_default_collection",
            "homepage_image_collection",
            "drill_intervals",
            "nytimes_api_key",
            "instagram_credentials",
            "google_calendar",
            "eye_candy"
        )
        widgets = {
            "google_calendar": Textarea(attrs={"class": "form-control"}),
            "nytimes_api_key": TextInput(attrs={"class": "form-control"}),
            "theme": Select(attrs={"class": "form-control form-select"})
        }
