from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource

from accounts.api import UserResource
from music.models import WishList


class MusicWishListResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = WishList.objects.all()
        resource_name = 'wishlist'
        authorization = Authorization()
