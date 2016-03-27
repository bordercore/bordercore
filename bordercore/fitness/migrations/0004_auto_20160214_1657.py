# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitness', '0003_exerciseuser'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='exerciseuser',
            unique_together=set([('user', 'exercise')]),
        ),
    ]
