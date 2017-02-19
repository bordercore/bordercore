import django
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.config.settings.prod'
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore')
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore/bordercore')

django.setup()

from music.models import Song


def test_album_songs_have_length_field():
    "Assert that all album songs have a length field"
    s = Song.objects.filter(length__isnull=True).filter(album__isnull=False)
    assert len(s) == 0, "%s songs fail this test" % len(s)
