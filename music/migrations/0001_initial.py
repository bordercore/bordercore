# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Album'
        db.create_table(u'music_album', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('artist', self.gf('django.db.models.fields.TextField')()),
            ('year', self.gf('django.db.models.fields.IntegerField')()),
            ('compilation', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('comment', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'music', ['Album'])

        # Adding model 'SongSource'
        db.create_table(u'music_songsource', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'music', ['SongSource'])

        # Adding model 'Song'
        db.create_table(u'music_song', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('artist', self.gf('django.db.models.fields.TextField')()),
            ('album', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['music.Album'])),
            ('track', self.gf('django.db.models.fields.IntegerField')()),
            ('year', self.gf('django.db.models.fields.IntegerField')()),
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('filename', self.gf('django.db.models.fields.TextField')()),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['music.SongSource'])),
            ('times_played', self.gf('django.db.models.fields.IntegerField')()),
            ('original_album', self.gf('django.db.models.fields.TextField')()),
            ('original_year', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'music', ['Song'])

        # Adding M2M table for field tags on 'Song'
        db.create_table(u'music_song_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('song', models.ForeignKey(orm[u'music.song'], null=False)),
            ('tag', models.ForeignKey(orm[u'tag.tag'], null=False))
        ))
        db.create_unique(u'music_song_tags', ['song_id', 'tag_id'])


    def backwards(self, orm):
        # Deleting model 'Album'
        db.delete_table(u'music_album')

        # Deleting model 'SongSource'
        db.delete_table(u'music_songsource')

        # Deleting model 'Song'
        db.delete_table(u'music_song')

        # Removing M2M table for field tags on 'Song'
        db.delete_table('music_song_tags')


    models = {
        u'music.album': {
            'Meta': {'object_name': 'Album'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'artist': ('django.db.models.fields.TextField', [], {}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'compilation': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        u'music.song': {
            'Meta': {'object_name': 'Song'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'album': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['music.Album']"}),
            'artist': ('django.db.models.fields.TextField', [], {}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'filename': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'original_album': ('django.db.models.fields.TextField', [], {}),
            'original_year': ('django.db.models.fields.IntegerField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['music.SongSource']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['tag.Tag']", 'symmetrical': 'False'}),
            'times_played': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'track': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        u'music.songsource': {
            'Meta': {'object_name': 'SongSource'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        u'tag.tag': {
            'Meta': {'object_name': 'Tag'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 3, 17, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True'})
        }
    }

    complete_apps = ['music']