from django.forms import ModelChoiceField, ModelForm, Select, TextInput

from accounts.models import UserProfile
from collection.models import Collection
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


# We need to create a custom class so that we can define what get's displayed in the select widget
class MyModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class UserProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        self.fields['homepage_default_collection'].label = "Default collection"
        self.fields['homepage_default_collection'].widget.attrs['class'] = 'form-control'
        self.fields['favorite_tags'].widget.attrs['class'] = 'form-control'
        self.fields['todo_default_tag'].widget.attrs['class'] = 'form-control'

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['favorite_tags'] = self.instance.get_tags()

    todo_default_tag = MyModelChoiceField(queryset=Tag.objects.filter(todo__isnull=False).distinct('name'), empty_label='Select Tag')

    homepage_default_collection = MyModelChoiceField(queryset=Collection.objects.exclude(name=''), empty_label='Select Collection')

    favorite_tags = ModelCommaSeparatedChoiceField(
        required=False,
        id='id_tags',
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = UserProfile
        fields = ('favorite_tags', 'todo_default_tag', 'homepage_default_collection', 'orgmode_file', 'google_calendar')
        widgets = {
            'orgmode_file': TextInput(attrs={'class': 'form-control'})
        }
