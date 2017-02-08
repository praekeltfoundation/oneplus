from django.test import TestCase
from django.core.urlresolvers import reverse
from communication.models import ChatGroup, ChatMessage
from organisation.models import Course, Organisation, School, Module, CourseModuleRel
from core.models import Class, Participant
from datetime import datetime, timedelta
from go_http.tests.test_send import RecordingHandler
import logging
from auth.models import Learner
from django.test.utils import override_settings


def create_course(name="course name", **kwargs):
    return Course.objects.create(name=name, **kwargs)


def create_class(name, course, **kwargs):
    return Class.objects.create(name=name, course=course, **kwargs)


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_school(name, organisation, **kwargs):
    return School.objects.create(
        name=name, organisation=organisation, **kwargs)


def create_learner(school, **kwargs):
    if 'grade' not in kwargs:
        kwargs['grade'] = 'Grade 11'
    return Learner.objects.create(school=school, **kwargs)


def create_participant(learner, classs, **kwargs):
    participant = Participant.objects.create(
        learner=learner, classs=classs, **kwargs)
    return participant


def create_module(name, course, **kwargs):
    module = Module.objects.create(name=name, **kwargs)
    rel = CourseModuleRel.objects.create(course=course, module=module)
    module.save()
    rel.save()
    return module


@override_settings(VUMI_GO_FAKE=True)
class TestCommunicationToUser(TestCase):

    def setUp(self):

        self.course = create_course()
        self.classs = create_class('class name', self.course)
        self.organisation = create_organisation()
        self.school = create_school('school name', self.organisation)
        self.learner = create_learner(
            self.school,
            username="+27123456789",
            mobile="+27123456789",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        self.handler = RecordingHandler()
        logger = logging.getLogger('DEBUG')
        logger.setLevel(logging.INFO)
        logger.addHandler(self.handler)
        self.participant = create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = create_module('module name', self.course)

    def test_sms_reset_link(self):
        resp = self.client.get(reverse('auth.sms_reset_password'), follow=True)
        self.assertEquals(resp.status_code, 200)

        # invalid form
        resp = self.client.post(
            reverse('auth.sms_reset_password'),
            {
                'msisdn': '',

            },
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please enter your mobile number.")

        # incorrect msisdn
        resp = self.client.post(
            reverse('auth.sms_reset_password'),
            {
                'msisdn': '+2712345678',

            },
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "The number you have entered is not registered.")

        # correct msisdn
        resp = self.client.post(
            reverse('auth.sms_reset_password'),
            {
                'msisdn': '%s' % self.learner.mobile

            },
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Link has been SMSed to you.")

    def test_inbox_send(self):
        self.client.get(reverse('auth.autologin',
                                kwargs={'token': self.learner.unique_token}))

        resp = self.client.get(reverse('com.inbox_send'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('com.inbox_send'),
            data={'comment': 'test'}, follow=True)

        self.assertEquals(resp.status_code, 200)

    def test_chatgroups(self):
        self.client.get(reverse('auth.autologin',
                                kwargs={'token': self.learner.unique_token}))

        group = ChatGroup.objects.create(
            name="Test",
            description="Test",
            course=self.course
        )

        ChatMessage.objects.create(
            chatgroup=group,
            author=self.learner,
            content="test",
            publishdate=datetime.now()
        )

        resp = self.client.get(reverse('com.chatgroups'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('com.chatgroups'))
        self.assertEquals(resp.status_code, 200)
