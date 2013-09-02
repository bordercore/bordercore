# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Author'
        db.create_table(u'book_author', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'book', ['Author'])

        # Adding model 'Book'
        db.create_table(u'book_book', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('subtitle', self.gf('django.db.models.fields.TextField')(null=True)),
            ('isbn', self.gf('django.db.models.fields.TextField')(null=True)),
            ('asin', self.gf('django.db.models.fields.TextField')(null=True)),
            ('year', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('publisher', self.gf('django.db.models.fields.TextField')(null=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True)),
            ('own', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'book', ['Book'])

        # Adding M2M table for field author on 'Book'
        db.create_table(u'book_book_author', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('book', models.ForeignKey(orm[u'book.book'], null=False)),
            ('author', models.ForeignKey(orm[u'book.author'], null=False))
        ))
        db.create_unique(u'book_book_author', ['book_id', 'author_id'])


    def backwards(self, orm):
        # Deleting model 'Author'
        db.delete_table(u'book_author')

        # Deleting model 'Book'
        db.delete_table(u'book_book')

        # Removing M2M table for field author on 'Book'
        db.delete_table('book_book_author')


    models = {
        u'book.author': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Author'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        u'book.book': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Book'},
            'asin': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'author': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['book.Author']", 'null': 'True', 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isbn': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'own': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'publisher': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'subtitle': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        }
    }

    complete_apps = ['book']