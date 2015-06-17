# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications
        spot_test = orm.GamificationBadgeTemplate.objects.create(name="Spot Test",
                                                                 image="img/OP_Badge_Event_01_SpotTest.png")
        five_spot_test = orm.GamificationBadgeTemplate.objects.create(name="5 Spot Tests",
                                                                      image="img/OP_Badge_Event_02_5SpotTests.png")
        exam = orm.GamificationBadgeTemplate.objects.create(name="Exam",
                                                            image="img/OP_Badge_Event_03_Exam.png")
        spot_test_champ = orm.GamificationBadgeTemplate.objects.create(name="Spot Test Champ",
                                                                       image="img/OP_Badge_Event_04_SpotTestChamp.png")
        exam_champ = orm.GamificationBadgeTemplate.objects.create(name="Exam Champ",
                                                                  image="img/OP_Badge_Event_05_ExamChamp.png")

        orm.GamificationScenario.objects.create(name="Spot Test", badge=spot_test, event="SPOT_TEST")
        orm.GamificationScenario.objects.create(name="5 Spot Tests", badge=five_spot_test, event="5_SPOT_TEST")
        orm.GamificationScenario.objects.create(name="Exam", badge=exam, event="EXAM")
        orm.GamificationScenario.objects.create(name="Spot Test Champ", badge=spot_test_champ, event="SPOT_TEST_CHAMP")
        orm.GamificationScenario.objects.create(name="Exam Champ", badge=exam_champ, event="EXAM_CHAMP")

    def backwards(self, orm):
        "Write your backwards methods here."
        orm.GamificationScenario.objects.filter(name="Spot Test").delete()
        orm.GamificationScenario.objects.filter(name="5 Spot Tests").delete()
        orm.GamificationScenario.objects.filter(name="Exam").delete()
        orm.GamificationScenario.objects.filter(name="Spot Test Champ").delete()
        orm.GamificationScenario.objects.filter(name="Exam Champ").delete()

        orm.GamificationBadgeTemplate.objects.filter(name="Spot Test").delete()
        orm.GamificationBadgeTemplate.objects.filter(name="5 Spot Tests").delete()
        orm.GamificationBadgeTemplate.objects.filter(name="Exam").delete()
        orm.GamificationBadgeTemplate.objects.filter(name="Spot Test Champ").delete()
        orm.GamificationBadgeTemplate.objects.filter(name="Exam Champ").delete()

    models = {
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
        }
    }

    complete_apps = ['gamification']
    symmetrical = True
