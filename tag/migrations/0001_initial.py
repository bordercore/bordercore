# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(unique=True)),
                ('is_meta', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=datetime.datetime(2015, 3, 8, 15, 15, 50, 262874))),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
