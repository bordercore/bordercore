# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fitness', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='weight',
            field=models.FloatField(),
            preserve_default=True,
        ),
    ]
