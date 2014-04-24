# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Gamification'
        db.delete_table(u'core_gamification')

        # Adding model 'GamificationScenario'
        db.create_table(u'core_gamificationscenario', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('module', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Module'], null=True)),
            ('event', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.GamificationPointBonus'], null=True, blank=True)),
            ('badge', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.GamificationBadgeTemplate'], null=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['GamificationScenario'])

        # Adding model 'GamificationPointBonus'
        db.create_table(u'core_gamificationpointbonus', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('image', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
            ('value', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
        ))
        db.send_create_signal(u'core', ['GamificationPointBonus'])

        # Adding model 'Participant'
        db.create_table(u'core_participant', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('learner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Learner'])),
            ('classs', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Class'])),
            ('datejoined', self.gf('django.db.models.fields.DateField')()),
            ('points', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'core', ['Participant'])

        # Adding M2M table for field pointbonus on 'Participant'
        m2m_table_name = db.shorten_name(u'core_participant_pointbonus')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('participant', models.ForeignKey(orm[u'core.participant'], null=False)),
            ('gamificationpointbonus', models.ForeignKey(orm[u'core.gamificationpointbonus'], null=False))
        ))
        db.create_unique(m2m_table_name, ['participant_id', 'gamificationpointbonus_id'])

        # Adding M2M table for field badgetemplate on 'Participant'
        m2m_table_name = db.shorten_name(u'core_participant_badgetemplate')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('participant', models.ForeignKey(orm[u'core.participant'], null=False)),
            ('gamificationbadgetemplate', models.ForeignKey(orm[u'core.gamificationbadgetemplate'], null=False))
        ))
        db.create_unique(m2m_table_name, ['participant_id', 'gamificationbadgetemplate_id'])

        # Adding model 'GamificationBadgeTemplate'
        db.create_table(u'core_gamificationbadgetemplate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('image', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
        ))
        db.send_create_signal(u'core', ['GamificationBadgeTemplate'])

        # Removing M2M table for field classes on 'Learner'
        db.delete_table(db.shorten_name(u'core_learner_classes'))


    def backwards(self, orm):
        # Adding model 'Gamification'
        db.create_table(u'core_gamification', (
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('module', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Module'], null=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'core', ['Gamification'])

        # Deleting model 'GamificationScenario'
        db.delete_table(u'core_gamificationscenario')

        # Deleting model 'GamificationPointBonus'
        db.delete_table(u'core_gamificationpointbonus')

        # Deleting model 'Participant'
        db.delete_table(u'core_participant')

        # Removing M2M table for field pointbonus on 'Participant'
        db.delete_table(db.shorten_name(u'core_participant_pointbonus'))

        # Removing M2M table for field badgetemplate on 'Participant'
        db.delete_table(db.shorten_name(u'core_participant_badgetemplate'))

        # Deleting model 'GamificationBadgeTemplate'
        db.delete_table(u'core_gamificationbadgetemplate')

        # Adding M2M table for field classes on 'Learner'
        m2m_table_name = db.shorten_name(u'core_learner_classes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('learner', models.ForeignKey(orm[u'core.learner'], null=False)),
            ('class', models.ForeignKey(orm[u'core.class'], null=False))
        ))
        db.create_unique(m2m_table_name, ['learner_id', 'class_id'])


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
        u'core.gamificationbadgetemplate': {
            'Meta': {'object_name': 'GamificationBadgeTemplate'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'})
        },
        u'core.gamificationpointbonus': {
            'Meta': {'object_name': 'GamificationPointBonus'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'value': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
        },
        u'core.gamificationscenario': {
            'Meta': {'object_name': 'GamificationScenario'},
            'badge': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.GamificationBadgeTemplate']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Module']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.GamificationPointBonus']", 'null': 'True', 'blank': 'True'})
        },
        u'core.learner': {
            'Meta': {'object_name': 'Learner'},
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
        u'core.participant': {
            'Meta': {'object_name': 'Participant'},
            'badgetemplate': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['core.GamificationBadgeTemplate']", 'symmetrical': 'False'}),
            'classs': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Class']"}),
            'datejoined': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'learner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Learner']"}),
            'pointbonus': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['core.GamificationPointBonus']", 'symmetrical': 'False'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {})
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