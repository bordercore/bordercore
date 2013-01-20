# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Feed'
        db.create_table('feed_feed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('last_check', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('last_response_code', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('homepage', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('feed', ['Feed'])

        # Adding model 'FeedItem'
        db.create_table('feed_feeditem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['feed.Feed'])),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('link', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('feed', ['FeedItem'])


    def backwards(self, orm):
        # Deleting model 'Feed'
        db.delete_table('feed_feed')

        # Deleting model 'FeedItem'
        db.delete_table('feed_feeditem')


    models = {
        'feed.feed': {
            'Meta': {'object_name': 'Feed'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_check': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'last_response_code': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        'feed.feeditem': {
            'Meta': {'object_name': 'FeedItem'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feed.Feed']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['feed']