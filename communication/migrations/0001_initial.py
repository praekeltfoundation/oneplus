# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    depends_on = (
        ("core", "0001_initial"),
    )

    def forwards(self, orm):
        # Adding model 'Page'
        db.create_table(u'communication_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisation.Course'], null=True)),
        ))
        db.send_create_signal(u'communication', ['Page'])

        # Adding model 'Post'
        db.create_table(u'communication_post', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisation.Course'], null=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('publishdate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'communication', ['Post'])

        # Adding model 'Discussion'
        db.create_table(u'communication_discussion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('publishdate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('moderated', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'communication', ['Discussion'])

        # Adding model 'Message'
        db.create_table(u'communication_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisation.Course'], null=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('publishdate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'communication', ['Message'])

        # Adding model 'ChatGroup'
        db.create_table(u'communication_chatgroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisation.Course'], null=True)),
        ))
        db.send_create_signal(u'communication', ['ChatGroup'])

        # Adding model 'ChatMessage'
        db.create_table(u'communication_chatmessage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chatgroup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['communication.ChatGroup'], null=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('publishdate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'communication', ['ChatMessage'])


    def backwards(self, orm):
        # Deleting model 'Page'
        db.delete_table(u'communication_page')

        # Deleting model 'Post'
        db.delete_table(u'communication_post')

        # Deleting model 'Discussion'
        db.delete_table(u'communication_discussion')

        # Deleting model 'Message'
        db.delete_table(u'communication_message')

        # Deleting model 'ChatGroup'
        db.delete_table(u'communication_chatgroup')

        # Deleting model 'ChatMessage'
        db.delete_table(u'communication_chatmessage')


    models = {
        u'communication.chatgroup': {
            'Meta': {'object_name': 'ChatGroup'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'communication.chatmessage': {
            'Meta': {'object_name': 'ChatMessage'},
            'chatgroup': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['communication.ChatGroup']", 'null': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'publishdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'communication.discussion': {
            'Meta': {'object_name': 'Discussion'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'publishdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'communication.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'publishdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'communication.page': {
            'Meta': {'object_name': 'Page'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'communication.post': {
            'Meta': {'object_name': 'Post'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'publishdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'organisation.course': {
            'Meta': {'object_name': 'Course'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'blank': 'True'})
        }
    }

    complete_apps = ['communication']