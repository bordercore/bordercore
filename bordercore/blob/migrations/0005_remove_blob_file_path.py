# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blob', '0004_auto_20150503_2116'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blob',
            name='file_path',
        ),
    ]
