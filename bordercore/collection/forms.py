from django.forms import ModelForm, Textarea, TextInput

from collection.models import Collection
from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag


class CollectionForm(ModelForm):
    def __init__(self, *args, **kwargs):

        super(CollectionForm, self).__init__(*args, **kwargs)

        # If this form has a model attached, get the tags and display them separated by commas
        if self.instance.id:
            self.initial['tags'] = self.instance.get_tags()

    tags = ModelCommaSeparatedChoiceField(
        required=False,
        queryset=Tag.objects.filter(),
        to_field_name='name')

    class Meta:
        model = Collection
        fields = ('name', 'description')
        widgets = {
            'description': Textarea(attrs={'class': 'form-control'}),
            'name': TextInput(attrs={'class': 'form-control'})
        }








