# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Learner'
        db.create_table(u'core_learner', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('firstname', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('lastname', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('school', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.School'], null=True)),
        ))
        db.send_create_signal(u'core', ['Learner'])

        # Adding M2M table for field classses on 'Learner'
        m2m_table_name = db.shorten_name(u'core_learner_classses')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('learner', models.ForeignKey(orm[u'core.learner'], null=False)),
            ('class', models.ForeignKey(orm[u'core.class'], null=False))
        ))
        db.create_unique(m2m_table_name, ['learner_id', 'class_id'])

        # Adding field 'Class.course'
        db.add_column(u'core_class', 'course',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Course'], null=True),
                      keep_default=False)

        # Adding field 'Class.type'
        db.add_column(u'core_class', 'type',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=1),
                      keep_default=False)

        # Adding field 'Class.startdate'
        db.add_column(u'core_class', 'startdate',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Class.enddate'
        db.add_column(u'core_class', 'enddate',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Learner'
        db.delete_table(u'core_learner')

        # Removing M2M table for field classses on 'Learner'
        db.delete_table(db.shorten_name(u'core_learner_classses'))

        # Deleting field 'Class.course'
        db.delete_column(u'core_class', 'course_id')

        # Deleting field 'Class.type'
        db.delete_column(u'core_class', 'type')

        # Deleting field 'Class.startdate'
        db.delete_column(u'core_class', 'startdate')

        # Deleting field 'Class.enddate'
        db.delete_column(u'core_class', 'enddate')


    models = {
        u'core.class': {
            'Meta': {'object_name': 'Class'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'enddate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'startdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
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
        u'core.learner': {
            'Meta': {'object_name': 'Learner'},
            'classses': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['core.Class']", 'symmetrical': 'False'}),
            'firstname': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastname': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'school': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.School']", 'null': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
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