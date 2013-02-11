from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie import fields
from bookmark.models import User, Bookmark

class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']
        allowed_methods = ['get']
        authorization = Authorization()

class BookmarkResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = Bookmark.objects.all()
        resource_name = 'bookmark'
        authorization = Authorization()
