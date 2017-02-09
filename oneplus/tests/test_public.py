from datetime import datetime, timedelta
from auth.models import Learner
from core.models import Class, Participant, TestingQuestion
from django.core.urlresolvers import reverse
from django.test import TestCase
from core.models import ParticipantBadgeTemplateRel
from gamification.models import GamificationBadgeTemplate, GamificationScenario
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
    return Learner.objects.create(school=school, **kwargs)


def create_participant(learner, classs, **kwargs):
    return Participant.objects.create(learner=learner, classs=classs, **kwargs)


def create_badgetemplate(name='badge template name', **kwargs):
    return GamificationBadgeTemplate.objects.create(
        name=name,
        image="none",
        **kwargs)


class TestPublicBadge(TestCase):
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

        self.badge_earned = create_badgetemplate(name='Earned Badge #1')
        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='LOGIN',
            course=self.course,
            module=self.module,
            badge=self.badge_earned
        )
        ParticipantBadgeTemplateRel.objects.create(participant=self.participant,
                                                   badgetemplate=self.badge_earned,
                                                   scenario=self.scenario)

        self.badge_await = create_badgetemplate(name='Awaiting Badge #1')

    def test_no_perm(self):
        self.learner.public_share = False
        self.learner.save()
        resp = self.client.get(
            '{}?p={}&b={}'.format(reverse('public:badges'), self.participant.id, self.badge_earned),
            follow=True)
        self.assertContains(resp, 'No one\'s home')

    def test_perm_earned(self):
        self.learner.public_share = True
        self.learner.save()
        resp = self.client.get(
            '{}?p={}&b={}'.format(reverse('public:badges'), self.participant.id, self.badge_earned.id),
            follow=True)
        self.assertContains(resp, self.badge_earned.name)
        self.assertContains(resp, 'has earned')

    def test_perm_unearned(self):
        self.learner.public_share = True
        self.learner.save()
        resp = self.client.get(
            '{}?p={}&b={}'.format(reverse('public:badges'), self.participant.id, self.badge_await.id),
            follow=True)
        self.assertContains(resp, self.badge_await.name)
        self.assertContains(resp, 'hasn\'t earned')
