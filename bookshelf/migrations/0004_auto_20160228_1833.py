# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('bookshelf', '0003_auto_20160228_1818'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookshelf',
            name='blob_list',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(null=True, blank=True), size=None),
        ),
    ]
