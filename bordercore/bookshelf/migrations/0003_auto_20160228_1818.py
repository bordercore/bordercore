# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('bookshelf', '0002_auto_20150912_1957'),
    ]

    migrations.RunSQL(
        """
        ALTER TABLE "bookshelf_bookshelf" ALTER COLUMN "blob_list" TYPE integer[] USING blob_list::integer[]
        """,
        state_operations=[
            migrations.AlterField(
                model_name='bookshelf',
                name='blob_list',
                field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(null=True, blank=True), size=None),
            ),
        ]
    )

    # operations = [
    #     migrations.AlterField(
    #         model_name='bookshelf',
    #         name='blob_list',
    #         field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(null=True, blank=True), size=None),
    #     ),
    # ]
