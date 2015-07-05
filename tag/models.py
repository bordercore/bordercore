from django.core.cache import cache
from django.db import models


class Tag(models.Model):
    name = models.TextField(unique=True)
    is_meta = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_meta_tags():
        tags = cache.get('meta_tags')
        if not tags:
            tags = Tag.objects.filter(is_meta=True)
            cache.set('meta_tags', tags)
        return [x.name for x in tags]
