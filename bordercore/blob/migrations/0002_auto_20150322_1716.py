# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blob', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blob',
            name='sha1sum',
            field=models.CharField(unique=True, max_length=40),
            preserve_default=True,
        ),
    ]
