# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'LearnerState.sumit_level'
        db.add_column(u'oneplus_learnerstate', 'sumit_level',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'LearnerState.sumit_question'
        db.add_column(u'oneplus_learnerstate', 'sumit_question',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'LearnerState.sumit_level'
        db.delete_column(u'oneplus_learnerstate', 'sumit_level')

        # Deleting field 'LearnerState.sumit_question'
        db.delete_column(u'oneplus_learnerstate', 'sumit_question')


    models = {
        u'auth.customuser': {
            'Meta': {'object_name': 'CustomUser'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'mobile': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'optin_email': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'optin_sms': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'unique_token': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'unique_token_expiry': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.learner': {
            'Meta': {'object_name': 'Learner', '_ormbases': [u'auth.CustomUser']},
            u'customuser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.CustomUser']", 'unique': 'True', 'primary_key': 'True'}),
            'enrolled': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'blank': 'True'}),
            'grade': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'last_active_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_maths_result': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'school': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.School']", 'null': 'True'}),
            'welcome_message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['communication.Sms']", 'null': 'True', 'blank': 'True'}),
            'welcome_message_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'communication.sms': {
            'Meta': {'object_name': 'Sms'},
            'date_sent': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'msisdn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'respond_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'responded': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['communication.SmsQueue']", 'null': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'})
        },
        u'communication.smsqueue': {
            'Meta': {'object_name': 'SmsQueue'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'msisdn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'send_date': ('django.db.models.fields.DateTimeField', [], {}),
            'sent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sent_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        u'content.testingquestion': {
            'Meta': {'ordering': "['name']", 'object_name': 'TestingQuestion'},
            'answer_content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'difficulty': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Module']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'question_content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'textbook_link': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.class': {
            'Meta': {'object_name': 'Class'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'enddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'startdate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        u'core.participant': {
            'Meta': {'object_name': 'Participant'},
            'badgetemplate': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['gamification.GamificationBadgeTemplate']", 'symmetrical': 'False', 'through': u"orm['core.ParticipantBadgeTemplateRel']", 'blank': 'True'}),
            'classs': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Class']"}),
            'datejoined': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'learner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Learner']"}),
            'pointbonus': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['gamification.GamificationPointBonus']", 'symmetrical': 'False', 'through': u"orm['core.ParticipantPointBonusRel']", 'blank': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'core.participantbadgetemplaterel': {
            'Meta': {'object_name': 'ParticipantBadgeTemplateRel'},
            'awarddate': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 6, 19, 0, 0)', 'null': 'True'}),
            'badgetemplate': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gamification.GamificationBadgeTemplate']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Participant']"}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gamification.GamificationScenario']"})
        },
        u'core.participantpointbonusrel': {
            'Meta': {'object_name': 'ParticipantPointBonusRel'},
            'awarddate': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 6, 19, 0, 0)', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Participant']"}),
            'pointbonus': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gamification.GamificationPointBonus']"}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gamification.GamificationScenario']"})
        },
        u'gamification.gamificationbadgetemplate': {
            'Meta': {'object_name': 'GamificationBadgeTemplate'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'gamification.gamificationpointbonus': {
            'Meta': {'object_name': 'GamificationPointBonus'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'value': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
        },
        u'gamification.gamificationscenario': {
            'Meta': {'object_name': 'GamificationScenario'},
            'badge': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gamification.GamificationBadgeTemplate']", 'null': 'True', 'blank': 'True'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Module']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gamification.GamificationPointBonus']", 'null': 'True', 'blank': 'True'})
        },
        u'oneplus.learnerstate': {
            'Meta': {'object_name': 'LearnerState'},
            'active_question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['content.TestingQuestion']", 'null': 'True'}),
            'active_result': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'golden_egg_question': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Participant']", 'null': 'True'}),
            'sumit_level': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'sumit_question': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'organisation.course': {
            'Meta': {'object_name': 'Course'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'question_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'blank': 'True'})
        },
        u'organisation.coursemodulerel': {
            'Meta': {'object_name': 'CourseModuleRel'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Module']"})
        },
        u'organisation.module': {
            'Meta': {'object_name': 'Module'},
            'courses': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'modules'", 'symmetrical': 'False', 'through': u"orm['organisation.CourseModuleRel']", 'to': u"orm['organisation.Course']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'module_link': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        u'organisation.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'organisation.school': {
            'Meta': {'object_name': 'School'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Organisation']", 'null': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['oneplus']