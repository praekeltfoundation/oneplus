# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from auth.models import Learner, CustomUser
from communication.models import Message, Discussion, ChatGroup, ChatMessage, Profanity, Post, PostComment, \
    CoursePostRel
from content.models import TestingQuestion, TestingQuestionOption, Event, SUMit, EventStartPage, EventEndPage, \
    EventSplashPage, EventQuestionRel, EventParticipantRel, EventQuestionAnswer, SUMitLevel
from core.models import Class, Participant, ParticipantQuestionAnswer, ParticipantRedoQuestionAnswer, \
    ParticipantBadgeTemplateRel, Setting
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.test import TestCase, Client
from django.test.utils import override_settings
from gamification.models import GamificationBadgeTemplate, GamificationPointBonus, GamificationScenario
from go_http.tests.test_send import RecordingHandler
from mock import patch
from oneplus.auth_views import space_available
from oneplus.learn_views import get_points_awarded, get_badge_awarded
from oneplus.models import LearnerState
from oneplus.tasks import update_perc_correct_answers_worker
from oneplus.templatetags.oneplus_extras import format_content, format_option
from oneplus.validators import validate_mobile
from oneplus.views import get_week_day
from organisation.models import Course, Module, CourseModuleRel, Organisation, School
from oneplus.tasks import reset_learner_states
from communication.utils import contains_profanity


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
            'mobile': '+27123455555'
        }
        resp = self.client.post(reverse('auth.edit_profile'), data=changes, follow=True)
        self.assertContains(resp, changes['first_name'], count=1)
        self.assertContains(resp, changes['last_name'], count=1)
        self.assertContains(resp, changes['mobile'], count=1)