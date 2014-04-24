# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'LearningSectionLink'
        db.delete_table(u'core_learningsectionlink')

        # Deleting model 'LearningSectionAudio'
        db.delete_table(u'core_learningsectionaudio')

        # Deleting model 'LearningSectionVideo'
        db.delete_table(u'core_learningsectionvideo')

        # Deleting model 'LearningSection'
        db.delete_table(u'core_learningsection')

        # Deleting model 'LearningSectionText'
        db.delete_table(u'core_learningsectiontext')

        # Deleting model 'LearningSectionImage'
        db.delete_table(u'core_learningsectionimage')

        # Adding field 'LearningChapter.content'
        db.add_column(u'core_learningchapter', 'content',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'LearningSectionLink'
        db.create_table(u'core_learningsectionlink', (
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionLink'])

        # Adding model 'LearningSectionAudio'
        db.create_table(u'core_learningsectionaudio', (
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionAudio'])

        # Adding model 'LearningSectionVideo'
        db.create_table(u'core_learningsectionvideo', (
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionVideo'])

        # Adding model 'LearningSection'
        db.create_table(u'core_learningsection', (
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('learningchapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.LearningChapter'], null=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'core', ['LearningSection'])

        # Adding model 'LearningSectionText'
        db.create_table(u'core_learningsectiontext', (
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionText'])

        # Adding model 'LearningSectionImage'
        db.create_table(u'core_learningsectionimage', (
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionImage'])

        # Deleting field 'LearningChapter.content'
        db.delete_column(u'core_learningchapter', 'content')


    models = {
        u'core.class': {
            'Meta': {'object_name': 'Class'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.course': {
            'Meta': {'object_name': 'Course'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'blank': 'True'})
        },
        u'core.discussion': {
            'Meta': {'object_name': 'Discussion'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.gamification': {
            'Meta': {'object_name': 'Gamification'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Module']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.learningchapter': {
            'Meta': {'object_name': 'LearningChapter'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Module']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.module': {
            'Meta': {'object_name': 'Module'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'core.page': {
            'Meta': {'object_name': 'Page'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.post': {
            'Meta': {'object_name': 'Post'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.school': {
            'Meta': {'object_name': 'School'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Organisation']", 'null': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'core.testing': {
            'Meta': {'object_name': 'Testing'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Module']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.testinggroup': {
            'Meta': {'object_name': 'TestingGroup'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.testingquestion': {
            'Meta': {'object_name': 'TestingQuestion'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.testingquestionfreeform': {
            'Meta': {'object_name': 'TestingQuestionFreeForm', '_ormbases': [u'core.TestingQuestion']},
            'content': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'testingquestion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.TestingQuestion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'core.testingquestionmultiplechoice': {
            'Meta': {'object_name': 'TestingQuestionMultipleChoice', '_ormbases': [u'core.TestingQuestion']},
            'content': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'testingquestion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.TestingQuestion']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['core']