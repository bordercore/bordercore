from django.forms import ModelChoiceField, ChoiceField, ModelForm, TextInput, ModelMultipleChoiceField

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

# We need to create a custom class so that we can define what get's displayed in the select widget
class MyModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class UserProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        self.fields['bookmarks_show_untagged_only'].label = "Show untagged bookmarks only"
        self.fields['favorite_tags'].widget.attrs['class'] = 'input-xxlarge'

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['favorite_tags'] = self.instance.get_tags()

    todo_default_tag = MyModelChoiceField(queryset=Tag.objects.filter(todo__isnull=False).distinct('name'), empty_label='Select Tag')

    favorite_tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = UserProfile
        fields = ('favorite_tags', 'bookmarks_show_untagged_only', 'todo_default_tag', 'orgmode_file')
        widgets = {
            'orgmode_file': TextInput(attrs={'class': 'form-control'})
        }
