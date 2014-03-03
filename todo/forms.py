from django.forms import ModelForm, Textarea, TextInput, ModelMultipleChoiceField

from todo.models import Todo
from tag.models import Tag

# http://stackoverflow.com/questions/5608576/django-enter-a-list-of-values-form-error-when-rendering-a-manytomanyfield-as-a
class ModelCommaSeparatedChoiceField(ModelMultipleChoiceField):

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


class TodoForm(ModelForm):
    def __init__(self, *args, **kwargs):

        # In case one of our views passed in the request object (eg from get_form_kwargs()),
        #  save it and remove it from kwargs before calling super()
        if kwargs.get('request'):
            request = kwargs.pop("request")

        super(TodoForm, self).__init__(*args, **kwargs)

        self.fields['is_urgent'].label = "Urgent"

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

    class Meta:
        model = Todo
        fields = ('task', 'note', 'url', 'due_date', 'is_urgent')
        widgets = {
            'task': TextInput(attrs={'class': 'input-xxlarge'}),
            'note': Textarea(attrs={'rows': 2, 'class': 'input-xxlarge'}),
            'url': TextInput(attrs={'class': 'input-xxlarge'}),
        }
