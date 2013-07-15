# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Feed.created'
        db.alter_column(u'feed_feed', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Feed.url'
        db.alter_column(u'feed_feed', 'url', self.gf('django.db.models.fields.URLField')(unique=True, max_length=200))

        # Changing field 'Feed.homepage'
        db.alter_column(u'feed_feed', 'homepage', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

    def backwards(self, orm):

        # Changing field 'Feed.created'
        db.alter_column(u'feed_feed', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Feed.url'
        db.alter_column(u'feed_feed', 'url', self.gf('django.db.models.fields.TextField')(unique=True))

        # Changing field 'Feed.homepage'
        db.alter_column(u'feed_feed', 'homepage', self.gf('django.db.models.fields.TextField')(null=True))

    models = {
        u'feed.feed': {
            'Meta': {'object_name': 'Feed'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_check': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'last_response_code': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'feed.feeditem': {
            'Meta': {'object_name': 'FeedItem'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['feed.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['feed']