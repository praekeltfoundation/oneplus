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


@override_settings(VUMI_GO_FAKE=True)
class GoldenEggTest(TestCase):

    def create_test_question(self, name, module, **kwargs):
        return TestingQuestion.objects.create(name=name,
                                              module=module,
                                              **kwargs)

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_module(self, name, course, **kwargs):
        module = Module.objects.create(name=name, **kwargs)
        rel = CourseModuleRel.objects.create(course=course, module=module)
        module.save()
        rel.save()
        return module

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_school(self, name, organisation, **kwargs):
        return School.objects.create(
            name=name, organisation=organisation, **kwargs)

    def create_learner(self, school, **kwargs):
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        participant = Participant.objects.create(
            learner=learner, classs=classs, **kwargs)

        return participant

    def create_badgetemplate(self, name='badge template name', **kwargs):
        return GamificationBadgeTemplate.objects.create(
            name=name,
            image="none",
            **kwargs)

    def create_gamification_point_bonus(self, name, value, **kwargs):
        return GamificationPointBonus.objects.create(
            name=name,
            value=value,
            **kwargs)

    def create_gamification_scenario(self, **kwargs):
        return GamificationScenario.objects.create(**kwargs)

    def create_test_question_option(self, name, question, correct=True):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=correct)

    def setUp(self):

        self.course = self.create_course()
        self.classs = self.create_class('class name', self.course)
        self.organisation = self.create_organisation()
        self.school = self.create_school('school name', self.organisation)
        self.learner = self.create_learner(
            self.school,
            username="+27123456789",
            mobile="+27123456789",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        self.participant = self.create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = self.create_module('module name', self.course)
        self.badge_template = self.create_badgetemplate()

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
        new_learner = self.create_learner(
            self.school,
            username="+27761234567",
            mobile="+27761234567",
            unique_token='123456789',
            unique_token_expiry=datetime.now() + timedelta(days=30))

        self.create_participant(new_learner, self.classs, datejoined=datetime.now())

        q = self.create_test_question('question_1', module=self.module, state=3)
        q_o = self.create_test_question_option('question_option_1', q)

        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': new_learner.unique_token})
        )

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
        golden_egg_badge = self.create_badgetemplate('golden egg')
        golden_egg_point = self.create_gamification_point_bonus('golden egg', 5)
        golden_egg_scenario = self.create_gamification_scenario(badge=golden_egg_badge, point=golden_egg_point)
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
