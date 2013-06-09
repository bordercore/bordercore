from django.forms import ModelForm, Textarea, TextInput, ValidationError, ModelMultipleChoiceField

from accounts.models import UserProfile
from tag.models import Tag

# http://stackoverflow.com/questions/5608576/django-enter-a-list-of-values-form-error-when-rendering-a-manytomanyfield-as-a
class ModelCommaSeparatedChoiceField(ModelMultipleChoiceField):
    widget = TextInput

    def clean(self, value):
        if value is not None:
            value = [item.strip() for item in value.split(",") if item.strip() != ''] # remove padding
        # Check if any of these tags are new.  The ORM won't create them for us, and in
        # fact will complain that the tag 'is not one of the available choices.'
        # These need to be explicitly created.
        for tag in value:
            newtag, created = Tag.objects.get_or_create(name=tag)
            if created:
                newtag.save()
        return super(ModelCommaSeparatedChoiceField, self).clean(value)

class UserProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        self.fields['bookmarks_show_untagged_only'].label = "Show untagged bookmarks only"

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['favorite_tags'] = self.instance.get_tags()

    favorite_tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = UserProfile
        fields = ('rss_feeds', 'favorite_tags', 'bookmarks_show_untagged_only')
        widgets = {
            'rss_feeds': TextInput(attrs={'class': 'input-xxlarge'}),
        }
