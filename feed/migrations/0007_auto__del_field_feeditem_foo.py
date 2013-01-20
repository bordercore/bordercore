# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'FeedItem.foo'
        db.delete_column('feed_feeditem', 'foo')


    def backwards(self, orm):
        # Adding field 'FeedItem.foo'
        db.add_column('feed_feeditem', 'foo',
                      self.gf('django.db.models.fields.IntegerField')(default=42),
                      keep_default=False)


    models = {
        'feed.feed': {
            'Meta': {'object_name': 'Feed'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
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