# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Organisation'
        db.create_table(u'core_organisation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
        ))
        db.send_create_signal(u'core', ['Organisation'])

        # Adding model 'School'
        db.create_table(u'core_school', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Organisation'], null=True)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
        ))
        db.send_create_signal(u'core', ['School'])

        # Adding model 'Course'
        db.create_table(u'core_course', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, blank=True)),
        ))
        db.send_create_signal(u'core', ['Course'])

        # Adding model 'Module'
        db.create_table(u'core_module', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Course'], null=True)),
        ))
        db.send_create_signal(u'core', ['Module'])

        # Adding model 'Class'
        db.create_table(u'core_class', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
        ))
        db.send_create_signal(u'core', ['Class'])

        # Adding model 'LearningChapter'
        db.create_table(u'core_learningchapter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('module', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Module'], null=True)),
        ))
        db.send_create_signal(u'core', ['LearningChapter'])

        # Adding model 'LearningSection'
        db.create_table(u'core_learningsection', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('learningchapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.LearningChapter'], null=True)),
        ))
        db.send_create_signal(u'core', ['LearningSection'])

        # Adding model 'LearningSectionText'
        db.create_table(u'core_learningsectiontext', (
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionText'])

        # Adding model 'LearningSectionImage'
        db.create_table(u'core_learningsectionimage', (
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionImage'])

        # Adding model 'LearningSectionLink'
        db.create_table(u'core_learningsectionlink', (
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionLink'])

        # Adding model 'LearningSectionVideo'
        db.create_table(u'core_learningsectionvideo', (
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionVideo'])

        # Adding model 'LearningSectionAudio'
        db.create_table(u'core_learningsectionaudio', (
            (u'learningsection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.LearningSection'], unique=True, primary_key=True)),
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'core', ['LearningSectionAudio'])

        # Adding model 'Testing'
        db.create_table(u'core_testing', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('module', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Module'], null=True)),
        ))
        db.send_create_signal(u'core', ['Testing'])

        # Adding model 'TestingGroup'
        db.create_table(u'core_testinggroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
        ))
        db.send_create_signal(u'core', ['TestingGroup'])

        # Adding model 'TestingQuestion'
        db.create_table(u'core_testingquestion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
        ))
        db.send_create_signal(u'core', ['TestingQuestion'])

        # Adding model 'TestingQuestionMultipleChoice'
        db.create_table(u'core_testingquestionmultiplechoice', (
            (u'testingquestion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.TestingQuestion'], unique=True, primary_key=True)),
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'core', ['TestingQuestionMultipleChoice'])

        # Adding model 'TestingQuestionFreeForm'
        db.create_table(u'core_testingquestionfreeform', (
            (u'testingquestion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.TestingQuestion'], unique=True, primary_key=True)),
            ('content', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'core', ['TestingQuestionFreeForm'])

        # Adding model 'Gamification'
        db.create_table(u'core_gamification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('module', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Module'], null=True)),
        ))
        db.send_create_signal(u'core', ['Gamification'])

        # Adding model 'Page'
        db.create_table(u'core_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Course'], null=True)),
        ))
        db.send_create_signal(u'core', ['Page'])

        # Adding model 'Post'
        db.create_table(u'core_post', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Course'], null=True)),
        ))
        db.send_create_signal(u'core', ['Post'])

        # Adding model 'Discussion'
        db.create_table(u'core_discussion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
        ))
        db.send_create_signal(u'core', ['Discussion'])


    def backwards(self, orm):
        # Deleting model 'Organisation'
        db.delete_table(u'core_organisation')

        # Deleting model 'School'
        db.delete_table(u'core_school')

        # Deleting model 'Course'
        db.delete_table(u'core_course')

        # Deleting model 'Module'
        db.delete_table(u'core_module')

        # Deleting model 'Class'
        db.delete_table(u'core_class')

        # Deleting model 'LearningChapter'
        db.delete_table(u'core_learningchapter')

        # Deleting model 'LearningSection'
        db.delete_table(u'core_learningsection')

        # Deleting model 'LearningSectionText'
        db.delete_table(u'core_learningsectiontext')

        # Deleting model 'LearningSectionImage'
        db.delete_table(u'core_learningsectionimage')

        # Deleting model 'LearningSectionLink'
        db.delete_table(u'core_learningsectionlink')

        # Deleting model 'LearningSectionVideo'
        db.delete_table(u'core_learningsectionvideo')

        # Deleting model 'LearningSectionAudio'
        db.delete_table(u'core_learningsectionaudio')

        # Deleting model 'Testing'
        db.delete_table(u'core_testing')

        # Deleting model 'TestingGroup'
        db.delete_table(u'core_testinggroup')

        # Deleting model 'TestingQuestion'
        db.delete_table(u'core_testingquestion')

        # Deleting model 'TestingQuestionMultipleChoice'
        db.delete_table(u'core_testingquestionmultiplechoice')

        # Deleting model 'TestingQuestionFreeForm'
        db.delete_table(u'core_testingquestionfreeform')

        # Deleting model 'Gamification'
        db.delete_table(u'core_gamification')

        # Deleting model 'Page'
        db.delete_table(u'core_page')

        # Deleting model 'Post'
        db.delete_table(u'core_post')

        # Deleting model 'Discussion'
        db.delete_table(u'core_discussion')


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
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Module']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.learningsection': {
            'Meta': {'object_name': 'LearningSection'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'learningchapter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.LearningChapter']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.learningsectionaudio': {
            'Meta': {'object_name': 'LearningSectionAudio', '_ormbases': [u'core.LearningSection']},
            'content': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'learningsection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.LearningSection']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'core.learningsectionimage': {
            'Meta': {'object_name': 'LearningSectionImage', '_ormbases': [u'core.LearningSection']},
            'content': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'learningsection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.LearningSection']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'core.learningsectionlink': {
            'Meta': {'object_name': 'LearningSectionLink', '_ormbases': [u'core.LearningSection']},
            'content': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'learningsection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.LearningSection']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'core.learningsectiontext': {
            'Meta': {'object_name': 'LearningSectionText', '_ormbases': [u'core.LearningSection']},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'learningsection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.LearningSection']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'core.learningsectionvideo': {
            'Meta': {'object_name': 'LearningSectionVideo', '_ormbases': [u'core.LearningSection']},
            'content': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'learningsection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.LearningSection']", 'unique': 'True', 'primary_key': 'True'})
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