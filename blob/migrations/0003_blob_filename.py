# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blob', '0002_auto_20150322_1716'),
    ]

    operations = [
        migrations.AddField(
            model_name='blob',
            name='filename',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
