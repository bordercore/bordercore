from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource

from accounts.api import UserResource
from todo.models import Todo


class TodoResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = Todo.objects.all()
        resource_name = 'todo'
        authorization = Authorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
