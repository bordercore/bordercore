from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm, Textarea, TextInput, ModelMultipleChoiceField

from bookmark.models import Bookmark, BookmarkTagUser
from blog.models import Tag

# http://stackoverflow.com/questions/5608576/django-enter-a-list-of-values-form-error-when-rendering-a-manytomanyfield-as-a
class ModelCommaSeparatedChoiceField(ModelMultipleChoiceField):
#    widget = TextInput(attrs={'class': 'form-control', 'data-role': '', 'data-provide': ''})

    widget = TextInput(attrs={'class': 'form-control typeahead', 'autocomplete': 'off'})

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
                if not old_tag.name in [new_tag.name for new_tag in new_tags]:
                    sorted_list = BookmarkTagUser.objects.get(tag=Tag.objects.get(name=old_tag.name), user=self.instance.user)
                    sorted_list.bookmark_list.remove(self.instance.id)
                    sorted_list.save()

        for new_tag in new_tags:
            print self.instance.user
            # Has the user already used this tag with any bookmarks?
            try:
                print self.instance.user
                sorted_list = BookmarkTagUser.objects.get(tag=Tag.objects.get(name=new_tag.name), user=self.instance.user)
                print "got here -- a"
                # Yes.  Now check if this bookmark already has this tag.
                if not self.instance.id in sorted_list.bookmark_list:
                    # Nope.  So this bookmark goes to the top of the sorted list.
                    sorted_list.bookmark_list.insert(0, self.instance.id)
                    sorted_list.save()
            except ObjectDoesNotExist:
                # This is the first time this tag has been applied to a bookmark.
                # Create a new list with one member (the current bookmark)
                print "foobar"
                sorted_list = BookmarkTagUser(tag=Tag.objects.get(name=new_tag.name),
                                              bookmark_list=[self.instance.id],
                                              user=self.instance.user)
                sorted_list.save()

        return new_tags

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = Bookmark
        fields = ('url', 'title', 'note', 'tags', 'id')
        widgets = {
            'url': TextInput(attrs={'class': 'form-control'}),
            'title': TextInput(attrs={'class': 'form-control'}),
            'note': Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }
