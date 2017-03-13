# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from auth.models import Learner
from content.models import TestingQuestion
from core.models import Class, Participant
from django.core.urlresolvers import reverse
from django.test import TestCase
from organisation.models import Course, Module, CourseModuleRel, Organisation, School


def create_test_question(name, module, **kwargs):
    return TestingQuestion.objects.create(name=name,
                                          module=module,
                                          **kwargs)


def create_course(name="course name", **kwargs):
    return Course.objects.create(name=name, **kwargs)


def create_module(name, course, **kwargs):
    module = Module.objects.create(name=name, **kwargs)
    rel = CourseModuleRel.objects.create(course=course, module=module)
    module.save()
    rel.save()
    return module


def create_class(name, course, **kwargs):
    return Class.objects.create(name=name, course=course, **kwargs)


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_school(name, organisation, **kwargs):
    return School.objects.create(name=name, organisation=organisation, **kwargs)


def create_learner(school, **kwargs):
    if 'grade' not in kwargs:
        kwargs['grade'] = 'Grade 11'
    if 'terms_accept' not in kwargs:
        kwargs['terms_accept'] = True
    return Learner.objects.create(school=school, **kwargs)


def create_participant(learner, classs, **kwargs):
    return Participant.objects.create(learner=learner, classs=classs, **kwargs)


class TestProfile(TestCase):
    def setUp(self):
        self.course = create_course()
        self.classs = create_class('class name', self.course)
        self.organisation = create_organisation()
        self.school = create_school('school name', self.organisation, province="Gauteng")
        self.learner = create_learner(
            self.school,
            username="+27123456789",
            first_name="Blarg",
            last_name="Honk",
            mobile="+27123456789",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        self.participant = create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = create_module('module name', self.course)

    def test_profile_page(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        #no questions
        resp = self.client.get(reverse('auth.profile'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, '"%s"' % (self.learner.first_name,))
        self.assertContains(resp, '"%s"' % (self.learner.last_name,))
        self.assertContains(resp, '"%s"' % (self.learner.mobile,))
        self.assertContains(resp, '"%s"' % (self.school.name,))
        self.assertContains(resp, '"%s"' % (self.school.province,))

    def test_profile_edit_get(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        #no fields completed
        resp = self.client.get(reverse('auth.edit_profile'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, '"%s"' % (self.learner.first_name,))
        self.assertContains(resp, '"%s"' % (self.learner.last_name,))
        self.assertContains(resp, '"%s"' % (self.learner.mobile,))
        self.assertContains(resp, '"%s"' % (self.school.name,))
        self.assertContains(resp, '"%s"' % (self.school.province,))

    def test_profile_edit_empty(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        #no fields completed
        resp = self.client.post(reverse('auth.edit_profile'), follow=True)
        self.assertContains(resp, 'This must be completed', count=3)

    def test_profile_edit_filled(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        #fields completed
        changes = {
            'first_name': 'Blargarg',
            'last_name': 'Honkonk',
            'mobile': '+27123455555',
            'public_share': True,
        }
        resp = self.client.post(reverse('auth.edit_profile'), data=changes, follow=True)
        self.assertContains(resp, changes['first_name'], count=1)
        self.assertContains(resp, changes['last_name'], count=1)
        self.assertContains(resp, changes['mobile'], count=1)
        l = Learner.objects.get(pk=self.learner.pk)
        self.assertTrue(l.public_share)
