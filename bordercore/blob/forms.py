import os

from django.forms import ModelForm, TextInput

from blob.models import Blob
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class BlobForm(ModelForm):

    def __init__(self, *args, **kwargs):

        # In case one of our views passed in the request object (eg from get_form_kwargs()),
        #  save it and remove it from kwargs before calling super()
        if kwargs.get('request'):
            request = kwargs.pop("request")

        super(BlobForm, self).__init__(*args, **kwargs)

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['tags'] = self.instance.get_tags()
        else:
            initial_tag = request.session.get('current_todo_tag', None)
            self.initial['tags'] = initial_tag

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    def clean_filename(self):
        data = self.cleaned_data['filename']
        if self.has_changed():
            parent_dir = self.instance.get_parent_dir()
            os.rename("%s/%s" % (parent_dir, self.initial['filename']), "%s/%s" % (parent_dir, data))
        return data

    class Meta:
        model = Blob
        fields = ('sha1sum', 'filename', 'tags')
        widgets = {
            'sha1sum': TextInput(attrs={'class': 'form-control'}),
            'filename': TextInput(attrs={'class': 'form-control'}),
            'tags': TextInput(attrs={'class': 'form-control'})
        }
