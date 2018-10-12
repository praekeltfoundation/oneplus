# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from auth.models import Learner, CustomUser
from content.models import TestingQuestion, TestingQuestionOption, GoldenEggRewardLog, GoldenEgg
from core.models import Class, Participant, ParticipantQuestionAnswer, ParticipantBadgeTemplateRel
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from gamification.models import GamificationBadgeTemplate, GamificationPointBonus, GamificationScenario
from go_http.tests.test_send import RecordingHandler
from mock import patch
from oneplus.models import LearnerState
from organisation.models import Course, Module, CourseModuleRel, Organisation, School
from oneplus.tasks import reset_learner_states


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
    return School.objects.create(
        name=name, organisation=organisation, **kwargs)


def create_learner(school, **kwargs):
    if 'grade' not in kwargs:
        kwargs['grade'] = 'Grade 11'
    if 'terms_accept' not in kwargs:
        kwargs['terms_accept'] = True
    return Learner.objects.create(school=school, **kwargs)


def create_participant(learner, classs, **kwargs):
    participant = Participant.objects.create(
        learner=learner, classs=classs, **kwargs)

    return participant


def create_badgetemplate(name='badge template name', **kwargs):
    return GamificationBadgeTemplate.objects.create(
        name=name,
        image="none",
        **kwargs)


def create_gamification_point_bonus(name, value, **kwargs):
    return GamificationPointBonus.objects.create(
        name=name,
        value=value,
        **kwargs)


def create_gamification_scenario(**kwargs):
    return GamificationScenario.objects.create(**kwargs)


def create_test_question_option(name, question, correct=True):
    return TestingQuestionOption.objects.create(
        name=name, question=question, correct=correct)


@override_settings(JUNEBUG_FAKE=True)
class GoldenEggTest(TestCase):

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
        self.participant = create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = create_module('module name', self.course)
        self.badge_template = create_badgetemplate()

        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='1_CORRECT',
            course=self.course,
            module=self.module,
            badge=self.badge_template
        )
        self.outgoing_vumi_text = []
        self.outgoing_vumi_metrics = []
        self.handler = RecordingHandler()
        logger = logging.getLogger('DEBUG')
        logger.setLevel(logging.INFO)
        logger.addHandler(self.handler)

        self.admin_user_password = 'mypassword'
        self.admin_user = CustomUser.objects.create_superuser(
            username='asdf33',
            email='asdf33@example.com',
            password=self.admin_user_password,
            mobile='+27111111133')

    def test_golden_egg(self):
        new_learner = create_learner(
            self.school,
            username="+27761234567",
            mobile="+27761234567",
            unique_token='123456789',
            unique_token_expiry=datetime.now() + timedelta(days=30))

        create_participant(new_learner, self.classs, datejoined=datetime.now())

        q = create_test_question('question_1', module=self.module, state=3)
        q_o = create_test_question_option('question_option_1', q)

        self.client.get(reverse('auth.autologin', kwargs={'token': new_learner.unique_token}))

        # GOLDEN EGG DOESN'T EXIST
        self.client.get(reverse('learn.next'))
        self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)
        new_participant = Participant.objects.filter(learner=new_learner).first()

        self.assertEquals(1, new_participant.points)
        log = GoldenEggRewardLog.objects.filter(participant=new_participant).count()
        self.assertEquals(0, log)

        ParticipantQuestionAnswer.objects.filter(participant=new_participant,
                                                 question=q,
                                                 option_selected=q_o).delete()
        new_participant.points = 0
        new_participant.save()

        # GOLDEN EGG INACTIVE
        golden_egg_badge = create_badgetemplate('golden egg')
        golden_egg_point = create_gamification_point_bonus('golden egg', 5)
        golden_egg_scenario = create_gamification_scenario(badge=golden_egg_badge, point=golden_egg_point)
        golden_egg = GoldenEgg.objects.create(course=self.course, classs=self.classs, active=False, point_value=5,
                                              badge=golden_egg_scenario)

        # set the golden egg number to 1
        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=new_participant).first()
        state.golden_egg_question = 1
        state.save()
        self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)
        new_participant = Participant.objects.filter(learner=new_learner).first()

        self.assertEquals(1, new_participant.points)
        log = GoldenEggRewardLog.objects.filter(participant=new_participant).count()
        self.assertEquals(0, log)

        ParticipantQuestionAnswer.objects.filter(participant=new_participant,
                                                 question=q,
                                                 option_selected=q_o).delete()
        new_participant.points = 0
        new_participant.save()

        # GOLDEN EGG ACTIVE - TEST POINTS - MONDAY
        golden_egg.active = True
        golden_egg.save()

        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=new_participant).first()
        state.golden_egg_question = 1
        state.save()

        with patch("oneplus.learn_views.LearnerState.get_week_day") as mock_get_week_day:
            mock_get_week_day.return_value = LearnerState.MONDAY
            with patch("oneplus.learn_views.LearnerState.today") as mock_today:
                mock_today.return_value = datetime(2015, 8, 24, 1, 0, 0)
                with patch("core.models.today") as mock_today2:
                    mock_today2.return_value = datetime(2015, 8, 24, 1, 0, 0)
                    self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)

        new_participant = Participant.objects.filter(learner=new_learner).first()

        self.assertEquals(11, new_participant.points)
        log = GoldenEggRewardLog.objects.filter(participant=new_participant, points=5).count()
        self.assertEquals(1, log)

        ParticipantQuestionAnswer.objects.filter(question=q).delete()
        ParticipantBadgeTemplateRel.objects.filter(participant=new_participant).delete()
        GoldenEggRewardLog.objects.filter(participant=new_participant).delete()

        new_participant.points = 0
        new_participant.save()

        # GOLDEN EGG ACTIVE - TEST POINTS
        # ANSWER MONDAY BUCKET QUESTION ON A TUESDAY and should not get awarded golden egg points.
        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=new_participant).first()
        state.golden_egg_question = 1
        state.save()

        with patch("oneplus.learn_views.LearnerState.get_week_day") as mock_get_week_day:
            mock_get_week_day.return_value = LearnerState.MONDAY + 1
            with patch("oneplus.learn_views.LearnerState.today") as mock_today:
                mock_today.return_value = datetime(2015, 8, 18, 1, 0, 0)
                with patch("core.models.today") as mock_today2:
                    mock_today2.return_value = datetime(2015, 8, 18, 1, 0, 0)
                    self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)

        new_participant = Participant.objects.get(learner=new_learner)

        self.assertEquals(1, new_participant.points)
        log = GoldenEggRewardLog.objects.filter(participant=new_participant, points=5).count()
        self.assertEquals(0, log)

        ParticipantQuestionAnswer.objects.filter(question=q).delete()
        ParticipantBadgeTemplateRel.objects.filter(participant=new_participant).delete()
        GoldenEggRewardLog.objects.filter(participant=new_participant).delete()

        new_participant.points = 0
        new_participant.save()

        # TEST AIRTIME
        self.client.get('/signout')
        self.client.get(reverse('auth.autologin', kwargs={'token': new_learner.unique_token}))
        golden_egg.point_value = None
        golden_egg.airtime = 5
        golden_egg.save()

        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=new_participant).first()
        state.golden_egg_question = 1
        state.save()

        with patch("oneplus.learn_views.LearnerState.get_week_day") as mock_get_week_day:
            mock_get_week_day.return_value = LearnerState.MONDAY
            with patch("oneplus.learn_views.LearnerState.today") as mock_today:
                mock_today.return_value = datetime(2015, 8, 24, 1, 0, 0)
                with patch("core.models.today") as mock_today2:
                    mock_today2.return_value = datetime(2015, 8, 24, 1, 0, 0)
                    self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)

        new_participant = Participant.objects.get(learner=new_learner)

        self.assertEquals(6, new_participant.points)

        log = GoldenEggRewardLog.objects.filter(participant=new_participant, airtime=5).count()
        self.assertEquals(1, log)

        ParticipantQuestionAnswer.objects.filter(question=q).delete()
        ParticipantBadgeTemplateRel.objects.filter(participant=new_participant).delete()
        GoldenEggRewardLog.objects.filter(participant=new_participant).delete()

        # TEST BADGE
        self.client.get('/signout')
        self.client.get(reverse('auth.autologin', kwargs={'token': new_learner.unique_token}))
        golden_egg.airtime = None
        golden_egg.badge = golden_egg_scenario
        golden_egg.save()

        new_participant.points = 0
        new_participant.save()

        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=new_participant).first()
        state.golden_egg_question = 1
        state.save()

        with patch("oneplus.learn_views.LearnerState.get_week_day") as mock_get_week_day:
            mock_get_week_day.return_value = LearnerState.MONDAY
            with patch("oneplus.learn_views.LearnerState.today") as mock_today:
                mock_today.return_value = datetime(2015, 8, 24, 1, 0, 0)
                with patch("core.models.today") as mock_today2:
                    mock_today2.return_value = datetime(2015, 8, 24, 1, 0, 0)
                    self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)

        new_participant = Participant.objects.filter(learner=new_learner).first()

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=golden_egg_badge,
            scenario=golden_egg_scenario
        ).count()

        self.assertEquals(6, new_participant.points)
        self.assertEquals(cnt, 1)
        log = GoldenEggRewardLog.objects.filter(participant=new_participant, badge=golden_egg_scenario).count()
        self.assertEquals(1, log)

        # Test Reset Task
        cnt = LearnerState.objects.filter(golden_egg_question__gt=0).count()
        self.assertEquals(1,cnt)

        reset_learner_states()

        cnt = LearnerState.objects.filter(golden_egg_question__gt=0).count()
        self.assertEquals(0,cnt)


@override_settings(JUNEBUG_FAKE=True)
class GoldenEggSplashTest(TestCase):

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
        self.participant = create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = create_module('module name', self.course)
        self.badge_template = create_badgetemplate()

        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='1_CORRECT',
            course=self.course,
            module=self.module,
            badge=self.badge_template
        )
        self.outgoing_vumi_text = []
        self.outgoing_vumi_metrics = []
        self.handler = RecordingHandler()
        logger = logging.getLogger('DEBUG')
        logger.setLevel(logging.INFO)
        logger.addHandler(self.handler)

        self.admin_user_password = 'mypassword'
        self.admin_user = CustomUser.objects.create_superuser(
            username='asdf33',
            email='asdf33@example.com',
            password=self.admin_user_password,
            mobile='+27111111133')

    def test_splash(self):

        q = create_test_question('question_1', module=self.module, state=3)
        q_o = create_test_question_option('question_option_1', q)

        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        self.client.get(reverse('learn.next'))
        golden_egg_badge = create_badgetemplate('golden egg')
        golden_egg_point = create_gamification_point_bonus('golden egg', 5)
        golden_egg_scenario = create_gamification_scenario(badge=golden_egg_badge, point=golden_egg_point)
        golden_egg = GoldenEgg.objects.create(course=self.course, classs=self.classs, active=True, point_value=5,
                                              badge=golden_egg_scenario)
        golden_egg.save()

        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=self.participant).first()
        state.golden_egg_question = 1
        state.save()

        resp = None
        with patch("oneplus.learn_views.LearnerState.get_week_day") as mock_get_week_day:
            mock_get_week_day.return_value = LearnerState.MONDAY
            with patch("oneplus.learn_views.LearnerState.today") as mock_today:
                mock_today.return_value = datetime(2015, 8, 24, 1, 0, 0)
                with patch("core.models.today") as mock_today2:
                    mock_today2.return_value = datetime(2015, 8, 24, 1, 0, 0)
                    resp = self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)

        self.assertRedirects(resp, reverse('learn.golden_egg_splash'))
        self.assertContains(resp, 'Golden Egg')

    def test_splash_wrong(self):

        q = create_test_question('question_1', module=self.module, state=3)
        q_o = create_test_question_option('question_option_1', q, correct=False)

        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        self.client.get(reverse('learn.next'))
        golden_egg_badge = create_badgetemplate('golden egg')
        golden_egg_point = create_gamification_point_bonus('golden egg', 5)
        golden_egg_scenario = create_gamification_scenario(badge=golden_egg_badge, point=golden_egg_point)
        golden_egg = GoldenEgg.objects.create(course=self.course, classs=self.classs, active=True, point_value=5,
                                              badge=golden_egg_scenario)
        golden_egg.save()

        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=self.participant).first()
        state.golden_egg_question = 1
        state.save()

        resp = None
        with patch("oneplus.learn_views.LearnerState.get_week_day") as mock_get_week_day:
            mock_get_week_day.return_value = LearnerState.MONDAY
            with patch("oneplus.learn_views.LearnerState.today") as mock_today:
                mock_today.return_value = datetime(2015, 8, 24, 1, 0, 0)
                with patch("core.models.today") as mock_today2:
                    mock_today2.return_value = datetime(2015, 8, 24, 1, 0, 0)
                    resp = self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)

        self.assertRedirects(resp, reverse('learn.wrong'))

        resp = self.client.get(reverse('learn.golden_egg_splash'), follow=True)
        self.assertRedirects(resp, reverse('learn.wrong'))
