# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Course.description'
        db.alter_column(u'organisation_course', 'description', self.gf('django.db.models.fields.CharField')(max_length=500))

        # Changing field 'Course.name'
        db.alter_column(u'organisation_course', 'name', self.gf('django.db.models.fields.CharField')(max_length=500, unique=True, null=True))

        # Changing field 'School.description'
        db.alter_column(u'organisation_school', 'description', self.gf('django.db.models.fields.CharField')(max_length=500))

        # Changing field 'School.name'
        db.alter_column(u'organisation_school', 'name', self.gf('django.db.models.fields.CharField')(max_length=500, unique=True, null=True))

        # Changing field 'Organisation.name'
        db.alter_column(u'organisation_organisation', 'name', self.gf('django.db.models.fields.CharField')(max_length=500, unique=True, null=True))

        # Changing field 'Organisation.description'
        db.alter_column(u'organisation_organisation', 'description', self.gf('django.db.models.fields.CharField')(max_length=500))

        # Changing field 'Module.description'
        db.alter_column(u'organisation_module', 'description', self.gf('django.db.models.fields.CharField')(max_length=500))

        # Changing field 'Module.name'
        db.alter_column(u'organisation_module', 'name', self.gf('django.db.models.fields.CharField')(max_length=500, unique=True, null=True))

    def backwards(self, orm):

        # Changing field 'Course.description'
        db.alter_column(u'organisation_course', 'description', self.gf('django.db.models.fields.CharField')(max_length=50))

        # Changing field 'Course.name'
        db.alter_column(u'organisation_course', 'name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, null=True))

        # Changing field 'School.description'
        db.alter_column(u'organisation_school', 'description', self.gf('django.db.models.fields.CharField')(max_length=50))

        # Changing field 'School.name'
        db.alter_column(u'organisation_school', 'name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, null=True))

        # Changing field 'Organisation.name'
        db.alter_column(u'organisation_organisation', 'name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, null=True))

        # Changing field 'Organisation.description'
        db.alter_column(u'organisation_organisation', 'description', self.gf('django.db.models.fields.CharField')(max_length=50))

        # Changing field 'Module.description'
        db.alter_column(u'organisation_module', 'description', self.gf('django.db.models.fields.CharField')(max_length=50))

        # Changing field 'Module.name'
        db.alter_column(u'organisation_module', 'name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, null=True))

    models = {
        u'organisation.course': {
            'Meta': {'object_name': 'Course'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'blank': 'True'})
        },
        u'organisation.module': {
            'Meta': {'object_name': 'Module'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True'})
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

    complete_apps = ['organisation']