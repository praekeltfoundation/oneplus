from datetime import datetime, timedelta
from auth.models import Learner
from core.models import Class, Participant, TestingQuestion
from django.core.urlresolvers import reverse
from django.test import TestCase
from core.models import ParticipantBadgeTemplateRel
from gamification.models import GamificationBadgeTemplate, GamificationScenario
from organisation.models import Course, Module, CourseModuleRel, Organisation, School
from django.test.utils import override_settings
from oneplus.public_views import get_learner_label


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


def create_badgetemplate(name='badge template name', **kwargs):
    return GamificationBadgeTemplate.objects.create(
        name=name,
        image="none",
        **kwargs)


@override_settings(SOCIAL_MEDIA_ACTIVE=True)
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

    @override_settings(SOCIAL_MEDIA_ACTIVE=False)
    def test_no_sm_badges(self):
        resp = self.client.get(
            '{0:s}?p={1:d}&b={2:d}'.format(reverse('public:badges'), 1, 1),
            follow=True)
        self.assertRedirects(resp, reverse('misc.onboarding'))

    def test_no_perm(self):
        self.learner.public_share = False
        self.learner.save()
        resp = self.client.get(
            '{0:s}?p={1:d}&b={2:d}'.format(reverse('public:badges'), self.participant.id, self.badge_earned.id),
            follow=True)
        self.assertContains(resp, 'No one\'s home')

    def test_perm_earned(self):
        self.learner.public_share = True
        self.learner.save()
        resp = self.client.get(
            '{0:s}?p={1:d}&b={2:d}'.format(reverse('public:badges'), self.participant.id, self.badge_earned.id),
            follow=True)
        self.assertContains(resp, self.badge_earned.name)
        self.assertContains(resp, 'has earned')
        self.assertContains(resp, '{0:s} {1:s}'.format(self.learner.first_name, self.learner.last_name))

    def test_perm_earned_no_last_name(self):
        last_name = self.learner.last_name
        self.learner.public_share = True
        self.learner.last_name = ''
        self.learner.save()
        resp = self.client.get(
            '{0:s}?p={1:d}&b={2:d}'.format(reverse('public:badges'), self.participant.id, self.badge_earned.id),
            follow=True)
        self.assertContains(resp, self.badge_earned.name)
        self.assertContains(resp, self.learner.first_name)
        self.assertNotContains(resp, last_name)
        self.assertContains(resp, 'has earned')
        self.assertContains(resp, self.learner.first_name)

    def test_perm_earned_no_names(self):
        first_name = self.learner.first_name
        last_name = self.learner.last_name
        self.learner.public_share = True
        self.learner.first_name = ''
        self.learner.last_name = ''
        self.learner.save()
        resp = self.client.get(
            '{0:s}?p={1:d}&b={2:d}'.format(reverse('public:badges'), self.participant.id, self.badge_earned.id),
            follow=True)
        self.assertContains(resp, self.badge_earned.name)
        self.assertContains(resp, 'Anon')
        self.assertNotContains(resp, first_name)
        self.assertNotContains(resp, last_name)
        self.assertContains(resp, 'has earned')

    def test_perm_unearned(self):
        self.learner.public_share = True
        self.learner.save()
        resp = self.client.get(
            '{0:s}?p={1:d}&b={2:d}'.format(reverse('public:badges'), self.participant.id, self.badge_await.id),
            follow=True)
        self.assertContains(resp, self.badge_await.name)
        self.assertContains(resp, 'hasn\'t earned')

    def test_invalid_badge(self):
        resp = self.client.get(
            '{0:s}?p={1:d}&b={2:s}'.format(reverse('public:badges'), self.participant.id, 'no_code'),
            follow=True)
        self.assertContains(resp, "No one's home")


@override_settings(SOCIAL_MEDIA_ACTIVE=True)
class TestPublicLevel(TestCase):
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
        self.participant = create_participant(self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = create_module('module name', self.course)

    @override_settings(SOCIAL_MEDIA_ACTIVE=False)
    def test_no_sm_level(self):
        resp = self.client.get(
            '{0:s}?p={1:d}'.format(reverse('public:level'), 1),
            follow=True)
        self.assertRedirects(resp, reverse('misc.onboarding'))

    def test_no_perm(self):
        self.learner.public_share = False
        self.learner.save()
        resp = self.client.get(
            '{0:s}?p={1:d}'.format(reverse('public:level'), self.participant.id),
            follow=True)
        self.assertContains(resp, 'No one\'s home')

    def test_lowest(self):
        self.learner.public_share = True
        self.learner.save()
        resp = self.client.get(
            '{0:s}?p={1:d}'.format(reverse('public:level'), self.participant.id),
            follow=True)
        self.assertContains(resp, 'Level')
        self.assertContains(resp,
                            '{0:s} {1:s}'.format(self.learner.first_name, self.learner.last_name))

    def test_lowest_no_last_name(self):
        last_name = self.learner.last_name
        self.learner.public_share = True
        self.learner.last_name = ''
        self.learner.save()
        resp = self.client.get(
            '{0:s}?p={1:d}'.format(reverse('public:level'), self.participant.id),
            follow=True)
        self.assertNotContains(resp, last_name)
        self.assertContains(resp, 'Level')
        self.assertContains(resp,
                            '{0:s} {1:s}'.format(self.learner.first_name, self.learner.last_name))

    def test_lowest_no_names(self):
        first_name = self.learner.first_name
        last_name = self.learner.last_name
        self.learner.first_name = ''
        self.learner.last_name = ''
        self.learner.public_share = True
        self.learner.save()
        resp = self.client.get(
            '{0:s}?p={1:d}'.format(reverse('public:level'), self.participant.id),
            follow=True)
        self.assertNotContains(resp, first_name)
        self.assertNotContains(resp, last_name)
        self.assertContains(resp, 'Level')
        self.assertContains(resp,
                            '{0:s} {1:s}'.format(self.learner.first_name, self.learner.last_name))

    def test_level_earned(self):
        self.learner.public_share = True
        self.learner.save()
        self.participant.points = 150
        self.participant.save()
        resp = self.client.get(
            '{0:s}?p={1:d}'.format(reverse('public:level'), self.participant.id),
            follow=True)
        self.assertContains(resp, 'Level')
        self.assertContains(resp,
                            '{0:s} {1:s} is {2:d} points away from Level {3:d}'.format(
                                self.learner.first_name, self.learner.last_name, 50, 3))

    def test_level_max(self):
        self.learner.public_share = True
        self.learner.save()
        self.participant.points = 750
        self.participant.save()
        resp = self.client.get(
            '{0:s}?p={1:d}'.format(reverse('public:level'), self.participant.id),
            follow=True)
        self.assertContains(resp, 'Level')
        self.assertContains(resp, '{0:s} {1:s} is awesome'.format(self.learner.first_name, self.learner.last_name))


@override_settings(SOCIAL_MEDIA_ACTIVE=True, JUNEBUG_SMS_FAKE=True)
class TestPublicLeaderboardSharing(TestCase):
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
            public_share=True,
            is_staff=True)
        self.participant = create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = create_module('module name', self.course)

    @override_settings(SOCIAL_MEDIA_ACTIVE=False)
    def test_no_sm_leader(self):
        resp = self.client.get("{0:s}?p={1:d}".format(reverse('public:leaderboard',
                                                              kwargs={"board_type": 'class'}),
                                                      1),
                               follow=True)
        self.assertRedirects(resp, reverse('misc.onboarding'))

    def test_leaderboard_class(self):
        #login learner
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        tmp_url = "{0:s}?p={1:d}".format(reverse('public:leaderboard', kwargs={"board_type": 'class'}),
                                         self.participant.id)
        resp = self.client.get(tmp_url)
        self.assertContains(resp, "position in the grade")

    def test_leaderboard_school(self):
        #login learner
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        tmp_url = "{0:s}?p={1:d}".format(reverse('public:leaderboard', kwargs={"board_type": 'school'}),
                                         self.participant.id)
        resp = self.client.get(tmp_url)
        self.assertContains(resp, "school's position")

    def test_leaderboard_national(self):
        #login learner
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        tmp_url = "{0:s}?p={1:d}".format(reverse('public:leaderboard', kwargs={"board_type": 'national'}),
                                         self.participant.id)
        resp = self.client.get(tmp_url)
        self.assertContains(resp, "national position")


class TestLearnerLabel(TestCase):
    def setUp(self):
        self.organisation = create_organisation()
        self.school = create_school('school name', self.organisation, province="Gauteng")
        self.learner = create_learner(
            self.school,
            username="+27123456789",
            mobile="+27123456789",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            public_share=True,
            is_staff=True)

    def test_get_learner_label_anon(self):
        label = get_learner_label(self.learner)
        self.assertEquals(label, 'Anon')

    def test_get_learner_label_first_name(self):
        self.learner.first_name = "blarg"
        self.learner.save()

        label = get_learner_label(self.learner)
        self.assertEquals(label, 'blarg')

    def test_get_learner_label_all_names(self):
        self.learner.first_name = "blarg"
        self.learner.last_name = "honk"
        self.learner.save()

        label = get_learner_label(self.learner)
        self.assertEquals(label, 'blarg honk')
