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
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('content', models.TextField()),
                ('title', models.TextField(null=True)),
                ('author', dbarray.fields.TextArrayField(blank=True)),
                ('source', models.TextField(null=True)),
                ('pub_date', models.DateField(null=True)),
                ('url', models.TextField(null=True)),
                ('sub_heading', models.TextField(null=True)),
                ('note', models.TextField(null=True)),
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
    ]
