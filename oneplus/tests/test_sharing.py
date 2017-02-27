from datetime import datetime, timedelta
from auth.models import Learner
from core.models import Class, Participant, TestingQuestion
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from gamification.models import GamificationBadgeTemplate
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


@override_settings(VUMI_GO_FAKE=True)
class TestLevelShare(TestCase):
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

    def test_no_public(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        self.learner.public_share = False
        self.learner.save()
        resp = self.client.get(reverse('share:level'), follow=True)
        self.assertRedirects(resp, reverse('learn.home'))

    def test_full_name(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        self.learner.public_share = True
        self.learner.save()
        self.participant.points = 10
        resp = self.client.get(reverse('share:level'), follow=True)
        self.assertContains(resp, 'Level')
        self.assertContains(resp, '{0:s} {1:s}'.format(self.learner.first_name, self.learner.last_name))

    def test_no_last_name(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        last_name = self.learner.last_name
        self.learner.public_share = True
        self.learner.last_name = ''
        self.learner.save()
        resp = self.client.get(reverse('share:level'), follow=True)
        self.assertNotContains(resp, last_name)
        self.assertContains(resp, 'Level')
        self.assertContains(resp,
                            '{0:s} {1:s}'.format(self.learner.first_name, self.learner.last_name))

    def test_lowest_no_names(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        first_name = self.learner.first_name
        last_name = self.learner.last_name
        self.learner.first_name = ''
        self.learner.last_name = ''
        self.learner.public_share = True
        self.learner.save()
        resp = self.client.get(reverse('share:level'), follow=True)
        self.assertNotContains(resp, first_name)
        self.assertNotContains(resp, last_name)
        self.assertContains(resp, 'Level')
        self.assertContains(resp,
                            '{0:s} {1:s}'.format(self.learner.first_name, self.learner.last_name))

    def test_level_earned(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        self.learner.public_share = True
        self.learner.save()
        self.participant.points = 150
        self.participant.save()
        resp = self.client.get(reverse('share:level'), follow=True)
        self.assertContains(resp, 'Level')
        self.assertContains(resp,
                            '{0:s} {1:s} is {2:d} points away from Level {3:d}'.format(
                                self.learner.first_name, self.learner.last_name, 50, 3))

    def test_level_max(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        self.learner.public_share = True
        self.learner.save()
        self.participant.points = 750
        self.participant.save()
        resp = self.client.get(reverse('share:level'), follow=True)
        self.assertContains(resp, 'Level')
        self.assertContains(resp, '{0:s} {1:s} is awesome'.format(self.learner.first_name, self.learner.last_name))


class TestPermissionToShare(TestCase):
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

    @override_settings(VUMI_GO_FAKE=True)
    def test_permission_badges(self):
        #login learner
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        # getting a badge
        bt1 = GamificationBadgeTemplate.objects.get(
            name="Level 1")

        #learner does not give permission to share
        self.learner.public_share = False
        self.learner.save()

        #go to page to share and share options must be disabled
        resp = self.client.get(reverse('prog.badges_single', kwargs={'badge_id': bt1.id}))
        self.assertContains(resp, "You will not be able to share")

        #update user gives permission to share publically
        self.learner.public_share = True
        self.learner.save()

        #go to share a badge and options should be there
        resp = self.client.get(reverse('prog.badges_single', kwargs={'badge_id': bt1.id}))
        self.assertContains(resp, "Share on")

    @override_settings(VUMI_GO_FAKE=True)
    def test_permission_levels(self):
        #login learner
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        #learner does not give permission to share
        self.learner.public_share = False
        self.learner.save()

        #go to home page to share level and button should not be there
        resp = self.client.get(reverse('learn.home'))
        self.assertNotContains(resp, "Share level")

        #update user gives permission to share publically
        self.learner.public_share = True
        self.learner.save()

        #go to share a badge and options should be there
        resp = self.client.get(reverse('learn.home'))
        self.assertContains(resp, "Share level")
