# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'TestingQuestionMultipleChoice'
        db.delete_table(u'core_testingquestionmultiplechoice')

        # Deleting model 'TestingQuestionFreeForm'
        db.delete_table(u'core_testingquestionfreeform')

        # Deleting model 'TestingGroup'
        db.delete_table(u'core_testinggroup')

        # Deleting model 'Testing'
        db.delete_table(u'core_testing')

        # Adding model 'TestingQuestionOption'
        db.create_table(u'core_testingquestionoption', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.TestingQuestion'], null=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('correct', self.gf('django.db.models.fields.BooleanField')()),
        ))
        db.send_create_signal(u'core', ['TestingQuestionOption'])

        # Adding model 'TestingBank'
        db.create_table(u'core_testingbank', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('module', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Module'], null=True)),
            ('question_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
        ))
        db.send_create_signal(u'core', ['TestingBank'])

        # Adding field 'TestingQuestion.order'
        db.add_column(u'core_testingquestion', 'order',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=1),
                      keep_default=False)

        # Adding field 'TestingQuestion.bank'
        db.add_column(u'core_testingquestion', 'bank',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.TestingBank'], null=True),
                      keep_default=False)

        # Adding field 'TestingQuestion.question_content'
        db.add_column(u'core_testingquestion', 'question_content',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Adding field 'TestingQuestion.answer_content'
        db.add_column(u'core_testingquestion', 'answer_content',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Adding field 'TestingQuestion.difficulty'
        db.add_column(u'core_testingquestion', 'difficulty',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=1),
                      keep_default=False)

        # Adding field 'TestingQuestion.points'
        db.add_column(u'core_testingquestion', 'points',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'LearningChapter.order'
        db.add_column(u'core_learningchapter', 'order',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=1),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'TestingQuestionMultipleChoice'
        db.create_table(u'core_testingquestionmultiplechoice', (
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            (u'testingquestion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.TestingQuestion'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'core', ['TestingQuestionMultipleChoice'])

        # Adding model 'TestingQuestionFreeForm'
        db.create_table(u'core_testingquestionfreeform', (
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            (u'testingquestion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.TestingQuestion'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'core', ['TestingQuestionFreeForm'])

        # Adding model 'TestingGroup'
        db.create_table(u'core_testinggroup', (
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, null=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'core', ['TestingGroup'])

        # Adding model 'Testing'
        db.create_table(u'core_testing', (
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('module', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Module'], null=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'core', ['Testing'])

        # Deleting model 'TestingQuestionOption'
        db.delete_table(u'core_testingquestionoption')

        # Deleting model 'TestingBank'
        db.delete_table(u'core_testingbank')

        # Deleting field 'TestingQuestion.order'
        db.delete_column(u'core_testingquestion', 'order')

        # Deleting field 'TestingQuestion.bank'
        db.delete_column(u'core_testingquestion', 'bank_id')

        # Deleting field 'TestingQuestion.question_content'
        db.delete_column(u'core_testingquestion', 'question_content')

        # Deleting field 'TestingQuestion.answer_content'
        db.delete_column(u'core_testingquestion', 'answer_content')

        # Deleting field 'TestingQuestion.difficulty'
        db.delete_column(u'core_testingquestion', 'difficulty')

        # Deleting field 'TestingQuestion.points'
        db.delete_column(u'core_testingquestion', 'points')

        # Deleting field 'LearningChapter.order'
        db.delete_column(u'core_learningchapter', 'order')


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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
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
        u'core.testingbank': {
            'Meta': {'object_name': 'TestingBank'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Module']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'question_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        u'core.testingquestion': {
            'Meta': {'object_name': 'TestingQuestion'},
            'answer_content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'bank': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.TestingBank']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'difficulty': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'question_content': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'core.testingquestionoption': {
            'Meta': {'object_name': 'TestingQuestionOption'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'correct': ('django.db.models.fields.BooleanField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.TestingQuestion']", 'null': 'True'})
        }
    }

    complete_apps = ['core']