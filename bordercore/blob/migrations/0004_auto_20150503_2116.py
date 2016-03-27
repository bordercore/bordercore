# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blob', '0003_blob_filename'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blob',
            name='file_path',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
    ]
