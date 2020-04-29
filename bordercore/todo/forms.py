from django.forms import ModelForm, Select, Textarea, TextInput

from lib.fields import ModelCommaSeparatedChoiceField
from tag.models import Tag
from todo.models import Todo


class TodoForm(ModelForm):
    def __init__(self, *args, **kwargs):

        # In case one of our views passed in the request object (eg from get_form_kwargs()),
        #  save it and remove it from kwargs before calling super()
        if kwargs.get('request'):
            request = kwargs.pop("request")

        super(TodoForm, self).__init__(*args, **kwargs)

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
        fields = ('task', 'priority', 'note', 'url', 'due_date')
        widgets = {
            'priority': Select(attrs={'class': 'form-control'}),
            'task': TextInput(attrs={'class': 'form-control'}),
            'note': Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'url': TextInput(attrs={'class': 'form-control'}),
        }
