# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("organisation", "0001_initial"),
    )

    def forwards(self, orm):
        # Adding model 'Permission'
        db.create_table(u'auth_permission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('codename', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'auth', ['Permission'])

        # Adding unique constraint on 'Permission', fields ['content_type', 'codename']
        db.create_unique(u'auth_permission', ['content_type_id', 'codename'])

        # Adding model 'Group'
        db.create_table(u'auth_group', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=80)),
        ))
        db.send_create_signal(u'auth', ['Group'])

        # Adding M2M table for field permissions on 'Group'
        m2m_table_name = db.shorten_name(u'auth_group_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['group_id', 'permission_id'])

        # Adding model 'CustomUser'
        db.create_table(u'auth_customuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('mobile', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('area', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('optin_sms', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('optin_email', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'auth', ['CustomUser'])

        # Adding M2M table for field groups on 'CustomUser'
        m2m_table_name = db.shorten_name(u'auth_customuser_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customuser', models.ForeignKey(orm[u'auth.customuser'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['customuser_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'CustomUser'
        m2m_table_name = db.shorten_name(u'auth_customuser_user_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customuser', models.ForeignKey(orm[u'auth.customuser'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['customuser_id', 'permission_id'])

        # Adding model 'SystemAdministrator'
        db.create_table(u'auth_systemadministrator', (
            (u'customuser_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.CustomUser'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'auth', ['SystemAdministrator'])

        # Adding model 'SchoolManager'
        db.create_table(u'auth_schoolmanager', (
            (u'customuser_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.CustomUser'], unique=True, primary_key=True)),
            ('school', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisation.School'], null=True)),
        ))
        db.send_create_signal(u'auth', ['SchoolManager'])

        # Adding model 'CourseManager'
        db.create_table(u'auth_coursemanager', (
            (u'customuser_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.CustomUser'], unique=True, primary_key=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisation.Course'], null=True)),
        ))
        db.send_create_signal(u'auth', ['CourseManager'])

        # Adding model 'CourseMentor'
        db.create_table(u'auth_coursementor', (
            (u'customuser_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.CustomUser'], unique=True, primary_key=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisation.Course'], null=True)),
        ))
        db.send_create_signal(u'auth', ['CourseMentor'])

        # Adding model 'Learner'
        db.create_table(u'auth_learner', (
            (u'customuser_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.CustomUser'], unique=True, primary_key=True)),
            ('school', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisation.School'], null=True)),
        ))
        db.send_create_signal(u'auth', ['Learner'])


    def backwards(self, orm):
        # Removing unique constraint on 'Permission', fields ['content_type', 'codename']
        db.delete_unique(u'auth_permission', ['content_type_id', 'codename'])

        # Deleting model 'Permission'
        db.delete_table(u'auth_permission')

        # Deleting model 'Group'
        db.delete_table(u'auth_group')

        # Removing M2M table for field permissions on 'Group'
        db.delete_table(db.shorten_name(u'auth_group_permissions'))

        # Deleting model 'CustomUser'
        db.delete_table(u'auth_customuser')

        # Removing M2M table for field groups on 'CustomUser'
        db.delete_table(db.shorten_name(u'auth_customuser_groups'))

        # Removing M2M table for field user_permissions on 'CustomUser'
        db.delete_table(db.shorten_name(u'auth_customuser_user_permissions'))

        # Deleting model 'SystemAdministrator'
        db.delete_table(u'auth_systemadministrator')

        # Deleting model 'SchoolManager'
        db.delete_table(u'auth_schoolmanager')

        # Deleting model 'CourseManager'
        db.delete_table(u'auth_coursemanager')

        # Deleting model 'CourseMentor'
        db.delete_table(u'auth_coursementor')

        # Deleting model 'Learner'
        db.delete_table(u'auth_learner')


    models = {
        u'auth.coursemanager': {
            'Meta': {'object_name': 'CourseManager', '_ormbases': [u'auth.CustomUser']},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']", 'null': 'True'}),
            u'customuser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.CustomUser']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'auth.coursementor': {
            'Meta': {'object_name': 'CourseMentor', '_ormbases': [u'auth.CustomUser']},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Course']", 'null': 'True'}),
            u'customuser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.CustomUser']", 'unique': 'True', 'primary_key': 'True'})
        },
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
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'optin_email': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'optin_sms': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
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
            'school': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.School']", 'null': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.schoolmanager': {
            'Meta': {'object_name': 'SchoolManager', '_ormbases': [u'auth.CustomUser']},
            u'customuser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.CustomUser']", 'unique': 'True', 'primary_key': 'True'}),
            'school': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.School']", 'null': 'True'})
        },
        u'auth.systemadministrator': {
            'Meta': {'object_name': 'SystemAdministrator', '_ormbases': [u'auth.CustomUser']},
            u'customuser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.CustomUser']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'organisation.course': {
            'Meta': {'object_name': 'Course'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'blank': 'True'})
        },
        u'organisation.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'organisation.school': {
            'Meta': {'object_name': 'School'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisation.Organisation']", 'null': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['auth']