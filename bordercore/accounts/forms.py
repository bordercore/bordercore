from django.forms import (ModelChoiceField, ModelForm, Select, Textarea,
                          TextInput)

from accounts.models import UserProfile
from collection.models import Collection
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class UserProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):

        # The request object is passed in from UserProfileUpdateView.get_form_kwargs()
        self.request = kwargs.pop("request", None)

        super(UserProfileForm, self).__init__(*args, **kwargs)

        # Don't be alarmed by the Tag.objects.all() queryset. Django will
        #  later filter this on just your favorite tags.
        self.fields['favorite_tags'] = ModelCommaSeparatedChoiceField(
            request=self.request,
            required=False,
            id='id_tags',
            queryset=Tag.objects.filter(user=self.request.user),
            to_field_name='name')
        self.initial['favorite_tags'] = self.instance.get_tags()
        self.fields['favorite_tags'].widget.attrs['class'] = 'form-control'

        self.fields['orgmode_file'].required = False

        collections_list = Collection.objects.filter(user=self.request.user).exclude(name="")
        if collections_list:
            self.fields['homepage_default_collection'] = ModelChoiceField(
                empty_label='Select Collection',
                label='Default collection',
                queryset=collections_list,
                required=False,
            )
            self.fields['homepage_default_collection'].widget.attrs['class'] = 'form-control'
        else:
            # If the user doesn't have any collections, remove the field
            self.fields.pop('homepage_default_collection')

        self.fields['todo_default_tag'] = ModelChoiceField(
            required=False,
            empty_label='Select Tag',
            queryset=Tag.objects.filter(user=self.request.user, todo__isnull=False).distinct('name'),
        )
        self.fields['todo_default_tag'].widget.attrs['class'] = 'form-control'

    class Meta:
        model = UserProfile
        fields = ('theme', 'sidebar_image', 'favorite_tags', 'todo_default_tag', 'homepage_default_collection', 'orgmode_file', 'google_calendar')
        widgets = {
            'google_calendar': Textarea(attrs={'class': 'form-control'}),
            'orgmode_file': TextInput(attrs={'class': 'form-control'}),
            'theme': Select(attrs={'class': 'form-control'})
        }
