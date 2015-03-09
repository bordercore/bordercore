# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tag', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.TextField()),
                ('artist', models.TextField()),
                ('year', models.IntegerField()),
                ('compilation', models.BooleanField(default=False)),
                ('comment', models.TextField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Listen',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Song',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.TextField()),
                ('artist', models.TextField()),
                ('track', models.IntegerField(null=True)),
                ('year', models.IntegerField(null=True)),
                ('length', models.IntegerField(null=True)),
                ('comment', models.TextField(null=True)),
                ('filename', models.TextField()),
                ('times_played', models.IntegerField(default=0, null=True)),
                ('original_album', models.TextField(null=True)),
                ('original_year', models.IntegerField(null=True)),
                ('album', models.ForeignKey(to='music.Album', null=True)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SongSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.TextField()),
                ('description', models.TextField()),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WishList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('song', models.TextField(null=True, blank=True)),
                ('artist', models.TextField(null=True)),
                ('album', models.TextField(null=True, blank=True)),
                ('note', models.TextField(null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='song',
            name='source',
            field=models.ForeignKey(to='music.SongSource'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='song',
            name='tags',
            field=models.ManyToManyField(to='tag.Tag'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='listen',
            name='song',
            field=models.ForeignKey(to='music.Song'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='listen',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='album',
            unique_together=set([('title', 'artist')]),
        ),
    ]
