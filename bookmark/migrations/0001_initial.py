# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import dbarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tag', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('url', models.TextField()),
                ('title', models.TextField()),
                ('note', models.TextField(null=True)),
                ('is_pinned', models.BooleanField(default=False)),
                ('last_check', models.DateTimeField(null=True)),
                ('last_response_code', models.IntegerField(null=True)),
                ('tags', models.ManyToManyField(to='tag.Tag')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookmarkTagUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bookmark_list', dbarray.fields.IntegerArrayField()),
                ('tag', models.ForeignKey(to='tag.Tag')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
