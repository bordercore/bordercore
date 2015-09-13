# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('bookshelf', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookshelf',
            name='blob_list',
            field=jsonfield.fields.JSONField(null=True, blank=True),
        ),
    ]
