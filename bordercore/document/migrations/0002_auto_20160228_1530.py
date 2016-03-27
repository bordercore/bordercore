# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='author',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(blank=True), size=None),
        ),
    ]
