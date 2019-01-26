from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.forms import CheckboxInput, ModelForm, Select, Textarea, TextInput, ValidationError

from bookmark.models import Bookmark, BookmarkTagUser
from tag.models import Tag
from lib.fields import ModelCommaSeparatedChoiceField


def daily_check_test(value):
    if value == 'null':
        return False
    else:
        return True


class BookmarkForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(BookmarkForm, self).__init__(*args, **kwargs)

        self.fields['note'].required = False
        self.fields['tags'].required = False

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['tags'] = self.instance.get_tags()

    def clean_tags(self):

        new_tags = self.cleaned_data.get('tags', None)

        # For existing bookmarks, check to see if the user is removing a tag.
        # If so, we need to remove it from the sorted list
        if self.instance.pk:
            for old_tag in self.instance.tags.all():
                if old_tag.name not in [new_tag.name for new_tag in new_tags]:
                    sorted_list = BookmarkTagUser.objects.get(tag=Tag.objects.get(name=old_tag.name), user=self.instance.user)
                    sorted_list.bookmark_list.remove(self.instance.id)
                    sorted_list.save()

        for new_tag in new_tags:
            # Has the user already used this tag with any bookmarks?
            try:
                sorted_list = BookmarkTagUser.objects.get(tag=Tag.objects.get(name=new_tag.name), user=self.instance.user)
                # Yes.  Now check if this bookmark already has this tag.
                if self.instance.id not in sorted_list.bookmark_list:
                    # Nope.  So this bookmark goes to the top of the sorted list.
                    sorted_list.bookmark_list.insert(0, self.instance.id)
                    sorted_list.save()
            except ObjectDoesNotExist:
                # This is the first time this tag has been applied to a bookmark.
                # Create a new list with one member (the current bookmark)
                sorted_list = BookmarkTagUser(tag=Tag.objects.get(name=new_tag.name),
                                              bookmark_list=[self.instance.id],
                                              user=self.instance.user)
                sorted_list.save()

        return new_tags

    def clean_url(self):
        data = self.cleaned_data['url']
        # Verify that this url is not a dupe.  Note: exclude current url when searching.
        b = Bookmark.objects.filter(user=self.instance.user, url=data).exclude(id=self.instance.id)
        if b:
            raise ValidationError("Error: this bookmark already exists")
        return data

    def clean_daily(self):
        data = self.cleaned_data['daily']
        return data

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = Bookmark
        fields = ('url', 'title', 'note', 'tags', 'importance', 'is_pinned', 'daily', 'id')
        widgets = {
            'url': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'title': TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'note': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'importance': Select(attrs={'class': 'form-control', 'autocomplete': 'off'}, choices=((1, 'Normal'), (5, 'High'), (10, 'Highest'))),
            'daily': CheckboxInput(check_test=daily_check_test)
        }
