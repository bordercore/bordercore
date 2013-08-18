from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource

from accounts.api import UserResource
from bookmark.models import Bookmark


class BookmarkResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = Bookmark.objects.all()
        resource_name = 'bookmark'
        authorization = Authorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
