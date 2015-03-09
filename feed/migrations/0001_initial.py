# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Feed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.TextField()),
                ('url', models.URLField(unique=True)),
                ('last_check', models.DateTimeField(null=True)),
                ('last_response_code', models.IntegerField(null=True)),
                ('homepage', models.URLField(null=True)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FeedItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField()),
                ('link', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('feed', models.ForeignKey(to='feed.Feed')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
