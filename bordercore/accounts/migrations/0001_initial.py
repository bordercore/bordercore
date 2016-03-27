# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import dbarray.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tag', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rss_feeds', dbarray.fields.IntegerArrayField()),
                ('bookmarks_show_untagged_only', models.BooleanField(default=False)),
                ('orgmode_file', models.TextField()),
                ('google_calendar', jsonfield.fields.JSONField()),
                ('favorite_tags', models.ManyToManyField(to='tag.Tag')),
                ('todo_default_tag', models.OneToOneField(related_name='default_tag', null=True, to='tag.Tag')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
