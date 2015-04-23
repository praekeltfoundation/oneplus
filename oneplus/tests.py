# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from datetime import datetime, timedelta, date
from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from datetime import datetime, timedelta
from core.models import Participant, Class, Course, ParticipantQuestionAnswer
from organisation.models import Organisation, School, Module, CourseModuleRel
from content.models import TestingQuestion, TestingQuestionOption
from gamification.models import GamificationScenario, GamificationBadgeTemplate
from auth.models import Learner, CustomUser
from django.test.client import Client
from communication.models import Message, ChatGroup, ChatMessage, Post, \
    Report, ReportResponse, Sms, SmsQueue, Discussion
from .templatetags.oneplus_extras import format_content, format_option
from mock import patch
from .models import LearnerState
from .views import get_points_awarded, get_badge_awarded, get_week_day
from .utils import get_today
from oneplus.admin import OnePlusLearnerAdmin, OnePlusLearnerResource
from go_http.tests.test_send import RecordingHandler
from django.conf import settings
from auth.admin import LearnerCreationForm
from django.test.utils import override_settings
import logging


@override_settings(VUMI_GO_FAKE=True)
class GeneralTests(TestCase):

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
        try:
            participant = Participant.objects.get(learner=learner)
        except Participant.DoesNotExist:
            participant = Participant.objects.create(
                learner=learner, classs=classs, **kwargs)

        return participant

    def create_test_question(self, name, module, **kwargs):
        return TestingQuestion.objects.create(name=name,
                                              module=module,
                                              **kwargs)

    def create_badgetemplate(self, name='badge template name', **kwargs):
        return GamificationBadgeTemplate.objects.create(
            name=name,
            image="none",
            **kwargs)

    def create_message(self, author, course, **kwargs):
        return Message.objects.create(author=author, course=course, **kwargs)

    def create_test_question_option(self, name, question, correct=True):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=correct)

    def create_test_answer(
            self,
            participant,
            question,
            option_selected,
            answerdate):
        return ParticipantQuestionAnswer.objects.create(
            participant=participant,
            question=question,
            option_selected=option_selected,
            answerdate=answerdate,
            correct=False
        )

    def create_and_answer_questions(self, num_questions, prefix, date):
        answers = []
        for x in range(0, num_questions):
            # Create a question
            question = self.create_test_question(
                'q' + prefix + str(x), self.module)

            question.save()
            option = self.create_test_question_option(
                'option_' + prefix + str(x),
                question)
            option.save()
            answer = self.create_test_answer(
                participant=self.participant,
                question=question,
                option_selected=option,
                answerdate=date
            )
            answer.save()
            answers.append(answer)

        return answers

    def create_question_report(self, _user, _question, _issue, _fix):
        return Report.objects.create(user=_user, question=_question, issue=_issue, fix=_fix)

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

    def test_get_next_question(self):
        self.create_test_question('question1', self.module)
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=None,
        )

        # get next question
        learnerstate.getnextquestion()
        learnerstate.save()

        # check active question
        self.assertEquals(learnerstate.active_question.name, 'question1')

    def test_home(self):
        self.create_test_question('question1', self.module)
        LearnerState.objects.create(
            participant=self.participant,
            active_question=None,
        )
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('learn.home'))
        self.assertEquals(resp.status_code, 200)

    def test_first_time(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('learn.first_time'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('learn.first_time'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_faq(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('misc.faq'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('misc.faq'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_terms(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('misc.terms'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('misc.terms'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def check_logs(self, msg):
        logs = self.handler.logs
        contains = [True for s in logs if msg == s.msg]
        return contains

    def assert_in_metric_logs(self, metric, aggr, value):
        msg = "Metric: '%s' [%s] -> %d" % (metric, aggr, value)
        logs = self.handler.logs
        contains = False
        if logs is not None:
            for log in logs:
                if msg == log.msg:
                    contains = True
                    break
        self.assertTrue(contains)

    def assert_not_in_metric_logs(self, metric, aggr, value):
        msg = "Metric: '%s' [%s] -> %d" % (metric, aggr, value)
        logs = self.handler.logs
        contains = False
        if logs is not None:
            for log in logs:
                if msg == log.msg:
                    contains = True
                    break
        self.assertFalse(contains)

    def test_fire_active_metric_first(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        self.client.get(reverse('learn.home'))
        self.assert_in_metric_logs('running.active.participants24', 'sum', 1)
        self.assert_in_metric_logs('running.active.participants48', 'sum', 1)
        self.assert_in_metric_logs('running.active.participants7', 'sum', 1)
        self.assert_in_metric_logs('running.active.participantsmonth', 'sum', 1)

    def test_fire_only24_hours_metric(self):
        # 24 hours metric has already been fired so only
        # 48, 7 days and month should fire
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        self.learner.last_active_date = (
            datetime.now() - timedelta(days=1, hours=4))
        self.learner.save()
        self.client.get(reverse('learn.home'))
        self.assert_in_metric_logs('running.active.participants24', 'sum', 1)
        self.assert_not_in_metric_logs('running.active.participants48', 'sum', 1)
        self.assert_not_in_metric_logs('running.active.participants7', 'sum', 1)
        self.assert_not_in_metric_logs('running.active.participantsmonth', 'sum', 1)

    def test_fire_24_and_48_hours_metric(self):
        # 24 hours metric has already been fired so only
        # 48, 7 days and month should fire
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        self.learner.last_active_date = (
            datetime.now() - timedelta(days=2, hours=4))
        self.learner.save()
        self.client.get(reverse('learn.home'))
        self.assert_in_metric_logs('running.active.participants24', 'sum', 1)
        self.assert_in_metric_logs('running.active.participants48', 'sum', 1)
        self.assert_not_in_metric_logs('running.active.participants7', 'sum', 1)
        self.assert_not_in_metric_logs('running.active.participantsmonth', 'sum', 1)

    def test_fire_24_and_48_7_days_hours_metric(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        self.learner.last_active_date = (
            datetime.now() - timedelta(days=8, hours=4))
        self.learner.save()
        self.client.get(reverse('learn.home'))
        self.assert_in_metric_logs('running.active.participants24', 'sum', 1)
        self.assert_in_metric_logs('running.active.participants48', 'sum', 1)
        self.assert_in_metric_logs('running.active.participants7', 'sum', 1)
        self.assert_not_in_metric_logs('running.active.participantsmonth', 'sum', 1)

    def test_fire_none_metric(self):
        # None should be fired
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        self.learner.last_active_date = (
            datetime.now() - timedelta(hours=4))
        self.learner.save()
        self.client.get(reverse('learn.home'))
        self.assert_not_in_metric_logs('running.active.participants24', 'sum', 1)
        self.assert_not_in_metric_logs('running.active.participants48', 'sum', 1)
        self.assert_not_in_metric_logs('running.active.participants7', 'sum', 1)
        self.assert_not_in_metric_logs('running.active.participantsmonth', 'sum', 1)

    def test_nextchallenge(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        question1 = self.create_test_question(
            'question1', self.module, question_content='test question')
        questionoption1 = TestingQuestionOption.objects.create(
            name='questionoption1',
            question=question1,
            content='questionanswer1',
            correct=True
        )

        resp = self.client.get(reverse('learn.next'))
        self.assertEquals(resp.status_code, 200)

        self.assertContains(resp, 'test question')
        self.assertContains(resp, 'questionanswer1')

        resp = self.client.post(
            reverse('learn.next'),
            data={'comment': 'test'}, follow=True)

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'test')

        disc = Discussion.objects.filter(content='test').first()

        resp = self.client.post(
            reverse('learn.next'),
            data={'reply': 'testreply', 'reply_button': disc.id}, follow=True)

        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse(
            'learn.next'),
            data={'page': 1},

            follow=True
        )

        self.assertEquals(resp.status_code, 200)

    def test_answer_correct_nextchallenge(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        # Create a question
        question1 = self.create_test_question(
            'question1', self.module, question_content='test question')
        option = TestingQuestionOption.objects.create(
            name='questionoption1',
            question=question1,
            content='questionanswer1',
            correct=True
        )

        # Create the learner state
        self.learner_state = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.learner_state.save()

        # Create
        resp = self.client.post(
            reverse('learn.next'),
            data={
                'answer': option.id
            }, follow=True)

        self.assertEquals(resp.status_code, 200)
        self.assert_in_metric_logs('total.questions', 'sum', 1)
        self.assert_in_metric_logs("questions.correct.24hr", 'last', 100)
        self.assert_in_metric_logs("questions.correct.48hr", 'last', 100)
        self.assert_in_metric_logs("questions.correct.7days", 'last', 100)
        self.assert_in_metric_logs("questions.correct.32days", 'last', 100)

    def test_answer_incorrect_nextchallenge(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        # Create a question
        question1 = self.create_test_question(
            'question1', self.module, question_content='test question')
        option = TestingQuestionOption.objects.create(
            name='questionoption1',
            question=question1,
            content='questionanswer1',
            correct=False
        )

        # Create the learner state
        self.learner_state = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.learner_state.save()

        # Create
        resp = self.client.post(
            reverse('learn.next'),
            data={
                'answer': option.id
            }, follow=True)

        self.assertEquals(resp.status_code, 200)
        self.assert_in_metric_logs('total.questions', 'sum', 1)
        self.assert_in_metric_logs("questions.correct.24hr", 'last', 0)
        self.assert_in_metric_logs("questions.correct.48hr", 'last', 0)
        self.assert_in_metric_logs("questions.correct.7days", 'last', 0)
        self.assert_in_metric_logs("questions.correct.32days", 'last', 0)

    def test_rightanswer(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )
        question1 = self.create_test_question(
            'question1',
            self.module,
            question_content='test question')
        option1 = self.create_test_question_option(
            name="option1",
            question=question1,
            correct=True
        )

        LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.participant.answer(question1, option1)

        resp = self.client.get(reverse('learn.right'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('learn.right'),
            data={'comment': 'test'}, follow=True)

        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse(
            'learn.right'),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

    def test_wronganswer(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token}))
        question1 = self.create_test_question(
            'question1',
            self.module,
            question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=False,
        )
        resp = self.client.get(reverse('learn.wrong'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('learn.wrong'),
            data={'comment': 'test'}, follow=True)

        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse(
            'learn.wrong'),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

    def test_report_question(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token}))

        question = self.create_test_question(
            'question1',
            self.module,
            question_content='test question')

        LearnerState.objects.create(
            participant=self.participant,
            active_question=question,
            active_result=True,
        )

        resp = self.client.get(reverse('learn.report_question', kwargs={'questionid': question.id, 'frm': 'next'}))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.get(reverse('learn.report_question', kwargs={'questionid': question.id, 'frm': 'right'}))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.get(reverse('learn.report_question', kwargs={'questionid': question.id, 'frm': 'wrong'}))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.get(reverse('learn.report_question', kwargs={'questionid': question.id, 'frm': 'bgg'}))
        self.assertEquals(resp.status_code, 302)

        resp = self.client.get(reverse('learn.report_question', kwargs={'questionid': 999, 'frm': 'next'}))
        self.assertEquals(resp.status_code, 302)

        resp = self.client.post(reverse('learn.report_question', kwargs={'questionid': question.id, 'frm': 'next'}),
                                data={'issue': 'Problem', 'fix': 'Solution'},
                                Follow=True)
        self.assertEquals(resp.status_code, 302)

        resp = self.client.post(
            reverse(
                'learn.report_question',
                kwargs={'questionid': question.id, 'frm': 'next'}
            ),
            data={'is': 'Problem', 'fi': 'Solution'},
            Follow=True
        )
        self.assertEquals(resp.status_code, 200)

    def test_inbox(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )
        msg = self.create_message(
            self.learner,
            self.course, name="msg",
            publishdate=datetime.now(),
            content='test message'
        )

        resp = self.client.get(reverse('com.inbox'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'test message')

        resp = self.client.post(
            reverse('com.inbox'),
            data={'hide': msg.id})
        self.assertEquals(resp.status_code, 200)

    def test_inbox_detail(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )
        msg = self.create_message(
            self.learner,
            self.course, name="msg",
            publishdate=datetime.now(),
            content='test message'
        )

        resp = self.client.get(
            reverse('com.inbox_detail', kwargs={'messageid': msg.id}))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'test message')

        resp = self.client.post(
            reverse('com.inbox_detail',
                    kwargs={'messageid': msg.id}),
            data={'hide': 'yes'})
        self.assertEquals(resp.status_code, 302)

    def test_chat(self):
        self.client.get(reverse('auth.autologin',
                                kwargs={'token': self.learner.unique_token}))
        chatgroup = ChatGroup.objects.create(
            name='testchatgroup',
            course=self.course
        )
        chatmsg1 = ChatMessage.objects.create(
            chatgroup=chatgroup,
            author=self.learner,
            content='chatmsg1content',
            publishdate=datetime.now()
        )

        resp = self.client.get(reverse(
            'com.chat',
            kwargs={'chatid': chatgroup.id})
        )
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'chatmsg1content')

        resp = self.client.post(reverse(
            'com.chat',
            kwargs={'chatid': chatgroup.id}),
            data={'comment': 'test'},
            follow=True
        )

        self.assertContains(resp, 'test')

        resp = self.client.post(reverse(
            'com.chat',
            kwargs={'chatid': chatgroup.id}),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

    def test_blog(self):
        self.client.get(reverse('auth.autologin',
                                kwargs={'token': self.learner.unique_token}))
        blog = Post.objects.create(
            name='testblog',
            course=self.course,
            publishdate=datetime.now()
        )
        blog.save()

        resp = self.client.get(reverse(
            'com.blog',
            kwargs={'blogid': blog.id})
        )
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse(
            'com.blog',
            kwargs={'blogid': blog.id})
        )
        self.assertEquals(resp.status_code, 200)

    def test_smspassword_get(self):
        resp = self.client.get(reverse('auth.smspassword'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def save_send_text_values(self, to_addr, content):
        self.outgoing_vumi_text.append((to_addr, content))

    def test_smspassword_post(self):
        resp = self.client.post(
            reverse('auth.smspassword'),
            {
                'msisdn': '+2712345678',

            },
            follow=True
        )

        self.assertEqual(resp.status_code, 200)

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

        resp = self.client.get(reverse('com.chatgroups'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('com.chatgroups'))
        self.assertEquals(resp.status_code, 200)

    @patch.object(LearnerState, 'today')
    def test_training_sunday(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 20, 0, 0, 0)

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_training_saturday(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 19, 0, 0, 0)

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')

        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_monday_first_week_no_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 21, 0, 0, 0)

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_monday_first_week_with_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 21, 0, 0, 0)

        self.create_and_answer_questions(
            3,
            'sunday',
            datetime(2014, 7, 20, 1, 1, 1))

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 0)

    @patch.object(LearnerState, 'today')
    def test_tuesday_with_monday(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 22, 1, 1, 1)

        self.create_and_answer_questions(
            3,
            'sunday',
            datetime(2014, 7, 21, 1, 1, 1))

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_miss_a_day_during_week(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 22, 0, 0, 0)

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 6)

    @patch.object(LearnerState, 'today')
    def test_miss_multiple_days_during_week(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 23, 0, 0, 0)
        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 9)

    @patch.object(LearnerState, 'today')
    def test_partially_miss_day_during_week(self, mock_get_today):
        monday = datetime(2014, 7, 21, 0, 0, 0)
        tuesday = datetime(2014, 7, 22, 0, 0, 0)

        # Tuesday the 22nd July
        mock_get_today.return_value = tuesday

        # Answer only 2 questions on Monday the 21st of July
        answers = self.create_and_answer_questions(
            2,
            'monday',
            datetime(2014, 7, 21, 1, 1, 1))

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        # Check answered
        answered = list(learnerstate.get_answers_this_week())

        self.assertListEqual(answered, answers)
        self.assertListEqual(learnerstate.get_week_range(), [monday, tuesday])

        # Should have 1 question from Monday and 3 from Tuesday, thus 4
        self.assertEquals(learnerstate.get_total_questions(), 4)

    @patch.object(LearnerState, 'today')
    def test_forget_a_single_days_till_weekend(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 26, 0, 0, 0)

        self.create_and_answer_questions(3, 'monday',
                                         datetime(2014, 7, 21, 1, 1, 1))
        self.create_and_answer_questions(3, 'tuesday',
                                         datetime(2014, 7, 22, 1, 1, 1))
        self.create_and_answer_questions(3, 'wednesday',
                                         datetime(2014, 7, 23, 1, 1, 1))
        self.create_and_answer_questions(3, 'thursday',
                                         datetime(2014, 7, 24, 1, 1, 1))

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_miss_all_days_till_weekend_except_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 26, 0, 0, 0)

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')
        self.create_and_answer_questions(3, 'training',
                                         datetime(2014, 7, 20, 1, 1, 1))
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 12)

    @patch.object(LearnerState, 'today')
    def test_miss_all_questions_except_training(self, mock_get_today):
        # Sunday the 28th
        mock_get_today.return_value = datetime(2014, 7, 28, 0, 0)

        question1 = self.create_test_question('question1', self.module,
                                              question_content='test question')

        # Answered 3 questions at training on Sunday the 20th
        self.create_and_answer_questions(3, 'training',
                                         datetime(2014, 7, 20, 1, 1, 1))
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEqual(learnerstate.is_training_week(), False)
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, "today")
    def test_saturday_no_questions_not_training(self, mock_get_today):
        learner = self.learner = self.create_learner(
            self.school,
            username="+27123456999",
            mobile="+2712345699",
            country="country",
            area="Test_Area",
            unique_token='abc1233',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        self.participant = self.create_participant(
            learner, self.classs,
            datejoined=datetime(2014, 8, 22, 0, 0, 0))

        mock_get_today.return_value = datetime(2014, 8, 23, 0, 0)

        # Create question
        question1 = self.create_test_question('q1', self.module)

        # Create and answer 2 other questions earlier in the day
        self.create_and_answer_questions(2, 'training',
                                         datetime(2014, 8, 23, 1, 22, 0))

        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        self.assertEquals(learnerstate.get_total_questions(), 3)
        self.assertEquals(learnerstate.get_num_questions_answered_today(), 2)

    def test_strip_p_tags(self):
        content = "<p><b>Test</b></p>"
        result = format_content(content)
        self.assertEquals(result, "<div><b>Test</b></div>")

    def test_align_image_only(self):
        content = "<img/>"
        result = format_option(content)
        self.assertEquals(result, u'<img style="vertical-align:middle"/>')

    def test_format_option_text_only(self):
        content = "Test"
        result = format_option(content)
        self.assertEquals(result, u'Test')

    def test_format_option_text_and_image(self):
        content = "<b>Test</b><img/>"
        result = format_option(content)
        self.assertEquals(result, u'<b>Test</b><img style='
                                  u'"vertical-align:middle"/>')

    def test_format_option_double_image(self):
        content = "<img/><img/>"
        result = format_option(content)
        self.assertEquals(result, u'<img style="vertical-align:middle"/>'
                                  u'<img style="vertical-align:middle"/>')

    def test_format_option(self):
        content = "<b>Test</b><p></p><img/>"
        output = format_option(content)
        self.assertEquals(output, u'<b>Test</b><br/><img style="'
                                  u'vertical-align:middle"/>')

    def test_format_content(self):
        content = '<img style="width:300px"/>'
        result = format_content(content)
        self.assertEquals(result, u'<div><img style="width:100%;'
                                  u'vertical-align:middle"/></div>')

    def test_already_format_content(self):
        content = '<img style="width:100%"/>'
        result = format_content(content)
        self.assertEquals(result, u'<div><img style="width:100%;'
                                  u'vertical-align:middle"/></div>')

    def test_format_content_small_image(self):
        content = '<img style="width:60px"/>'
        result = format_content(content)
        self.assertEquals(result, u'<div><img style="width:60px;'
                                  u'vertical-align:middle"/></div>')

    def test_filters_empty(self):
        content = ""
        output = format_content(content)
        self.assertEquals(output, u'<div></div>')

    def test_filters_empty_option(self):
        content = ""
        output = format_option(content)
        self.assertEquals(output, u'')

    def test_unicode_input(self):
        content = u'Zoë'
        output = format_option(content)
        self.assertEquals(output, u'Zoë')

    def test_save_then_display(self):
        testingquestion = TestingQuestion.objects.create()
        testingquestion.question_content = "There are 52 cards " \
                                           "in a playing deck of cards. " \
                                           "There are four Kings. " \
                                           "If you draw out one card, " \
                                           "the probability " \
                                           "that it will be a King is: "
        testingquestion.save()

        self.assertEquals(testingquestion.question_content,
                          u'<div>There are 52 cards '
                          u'in a playing deck of cards. '
                          u'There are four Kings. '
                          u'If you draw out one card, '
                          u'the probability '
                          u'that it will be a King is: </div>')

        content = format_content(testingquestion.question_content)

        self.assertEquals(content,
                          u'<div>There are 52 cards '
                          u'in a playing deck of cards. '
                          u'There are four Kings. '
                          u'If you draw out one card, '
                          u'the probability '
                          u'that it will be a King is: </div>')

    def test_save_then_display(self):
        testingquestionoption = TestingQuestionOption.objects.create(
            correct=True)
        testingquestionoption.content = "<img>"
        testingquestionoption.save()

        self.assertEquals(testingquestionoption.content,
                          u'<img style="vertical-align:middle"/>')

        content = format_option(testingquestionoption.content)

        self.assertEquals(content, u'<img style="vertical-align:middle"/>')

    def test_right_view(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        question = self.create_test_question('question1', self.module,
                                             question_content='test question')
        questionoption = self.create_test_question_option('questionoption1',
                                                          question)

        # Post a correct answer
        self.client.post(
            reverse('learn.next'),
            data={'answer': questionoption.id},
        )
        point = get_points_awarded(self.participant)
        badge, badge_points = get_badge_awarded(self.participant)
        self.assertEqual(point, 1)
        self.assertEqual(badge, self.badge_template)

    def test_view_adminpreview(self):

        password = 'mypassword'
        my_admin = CustomUser.objects.create_superuser(
            username='asdf',
            email='asdf@example.com',
            password=password,
            mobile='+27111111111')
        c = Client()
        c.login(username=my_admin.username, password=password)

        self.question = self.create_test_question(
            'question1',
            self.module,
            question_content='test question')
        self.questionoption = self.create_test_question_option(
            'questionoption1',
            self.question)

        resp = c.get(
            reverse(
                'learn.preview',
                kwargs={
                    'questionid': self.question.id}))

        self.assertContains(resp, "test question")

        # Post a correct answer
        resp = c.post(
            reverse('learn.preview', kwargs={'questionid': self.question.id}),
            data={'answer': self.questionoption.id}, follow=True
        )

        self.assertContains(resp, "Correct")

    def test_right_view_adminpreview(self):

        password = 'mypassword'
        my_admin = CustomUser.objects.create_superuser(
            username='asdf',
            email='asdf@example.com',
            password=password,
            mobile='+27111111111')
        c = Client()
        resp = c.login(username=my_admin.username, password=password)

        self.question = self.create_test_question(
            'question1',
            self.module,
            question_content='test question')
        self.questionoption = self.create_test_question_option(
            'questionoption1',
            self.question)

        resp = c.get(
            reverse(
                'learn.preview.right',
                kwargs={
                    'questionid': self.question.id}))

        self.assertContains(resp, "Correct")

    def test_wrong_view_adminpreview(self):

        password = 'mypassword'
        my_admin = CustomUser.objects.create_superuser(
            username='asdf',
            email='asdf@example.com',
            password=password,
            mobile='+27111111111')
        c = Client()
        c.login(username=my_admin.username, password=password)

        self.question = self.create_test_question(
            'question1',
            self.module,
            question_content='test question')

        self.questionoption = self.create_test_question_option(
            'questionoption1',
            self.question)

        resp = c.get(
            reverse(
                'learn.preview.wrong',
                kwargs={
                    'questionid': self.question.id}))

        self.assertContains(resp, "Incorrect")

    def test_wrong_view(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        question = self.create_test_question(
            'question1', self.module,
            question_content='test question')

        self.create_test_question_option(
            'questionoption1',
            question)

        questionoption2 = self.create_test_question_option(
            "questionoption2",
            question,
            correct=False)

        # Post a incorrect answer
        resp = self.client.post(
            reverse('learn.next'),
            data={'answer': questionoption2.id},
            follow=True
        )
        self.assertContains(resp, "Incorrect")

    def test_welcome_screen(self):
        resp = self.client.get(reverse('misc.welcome'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('misc.welcome'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_about_screen(self):
        resp = self.client.get(reverse('misc.about'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('misc.about'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_contact_screen(self):
        resp = self.client.get(reverse('misc.contact'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('misc.contact'), follow=True)
        self.assertContains(resp, "Please complete the following fields:")

    def test_get_week_day(self):
        day = get_week_day()
        self.assertLess(day, 7)
        self.assertGreaterEqual(day, 0)

    def test_menu_screen(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('core.menu'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('core.menu'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_login(self):
        resp = self.client.get(reverse('auth.login'))
        self.assertEquals(resp.status_code, 200)

        password = 'mypassword'
        my_admin = CustomUser.objects.create_superuser(
            username='asdf',
            email='asdf@example.com',
            password=password,
            mobile='+27111111111')

        c = Client()
        c.login(username=my_admin.username, password=password)

        resp = c.post(reverse('auth.login'), data={
            'username': "+27198765432",
            'password': password},
            follow=True)

        self.assertContains(resp, "OnePlus is currently in test phase")

        learner = Learner.objects.create_user(
            username="+27231231231",
            mobile="+27231231231",
            password='1234'
        )
        learner.save()

        resp = c.post(reverse('auth.login'), data={
            'username': "+27231231231",
            'password': '1234'},
            follow=True)
        self.assertContains(resp, "You are not currently linked to a class")

        self.create_participant(
            learner,
            self.classs,
            datejoined=datetime.now())

        resp = c.post(reverse('auth.login'), data={
            'username': "+27231231231",
            'password': '1235'},
            follow=True)

        self.assertContains(resp, "incorrect password")

        resp = c.post(reverse('auth.login'), data={
            'username': "+27231231231",
            'password': '1234'},
            follow=True)

        self.assertContains(resp, "WELCOME")

    def test_points_screen(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('prog.points'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.points'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_leaderboard_screen(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('prog.leader'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.leader'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_ontrack_screen(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('prog.ontrack'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.ontrack'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_bloglist_screen(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('com.bloglist'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('com.bloglist'), follow=True)
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse(
            'com.bloglist'),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

    def test_smspassword_get(self):
        resp = self.client.get(reverse('auth.smspassword'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def save_send_text_values(self, to_addr, content):
        self.outgoing_vumi_text.append((to_addr, content))

    def test_bloghero_screen(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('com.bloghero'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('com.bloghero'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_badge_screen(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('prog.badges'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.badges'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_signout_screen(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('auth.signout'))
        self.assertEquals(resp.status_code, 302)

        resp = self.client.post(reverse('auth.signout'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_dashboard(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get(reverse('dash.board'))
        self.assertContains(resp, 'sapphire')

    def test_dashboard_data(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get(reverse('dash.data'))
        self.assertContains(resp, 'num_email_optin')

        resp = c.post(reverse('dash.data'))
        self.assertContains(resp, 'post office')

    def test_question_difficulty_report(self):

        def make_content(ftype):
            d = datetime.now().date().strftime('%Y_%m_%d')
            file_name_base = 'question_difficulty_report'
            file_name = '%s_%s.%s' % (file_name_base, d, ftype)
            return 'attachment; filename="%s"' % file_name

        question1 = self.create_test_question(
            'question1',
            self.module,
            question_content='test question')
        option1 = self.create_test_question_option(
            name="option1",
            question=question1,
            correct=True
        )

        LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.participant.answer(question1, option1)

        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        resp = c.get(reverse('reports.question_difficulty', kwargs={'mode': 1}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv'))

        resp = c.get(reverse('reports.question_difficulty', kwargs={'mode': 2}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('xls'))

        resp = c.get(reverse('reports.question_difficulty', kwargs={'mode': 3}))
        self.assertEquals(resp.status_code, 302)

    def test_reports_page(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get(reverse('reports.home'))
        self.assertContains(resp, 'ONEPLUS')

    def test_report_learner(self):
        def make_content(ftype, region=None):
            d = datetime.now().date().strftime('%Y_%m_%d')
            file_name_base = 'learner_report'

            if region is not None:
                file_name_base = '%s_%s' % (file_name_base, region)

            file_name = '%s_%s.%s' % (file_name_base, d, ftype)
            return 'attachment; filename="%s"' % file_name

        question1 = self.create_test_question(
            'question1',
            self.module,
            question_content='test question')
        option1 = self.create_test_question_option(
            name="option1",
            question=question1,
            correct=True
        )

        LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.participant.answer(question1, option1)

        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        #csv no region
        resp = c.get(reverse('reports.learner', kwargs={'mode': 1, 'region': ''}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv'))

        #xls no region
        resp = c.get(reverse('reports.learner', kwargs={'mode': 2, 'region': ''}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('xls'))

        #csv + region
        resp = c.get(reverse('reports.learner', kwargs={'mode': 1, 'region': 'Test_Area'}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv', 'Test_Area'))
        self.assertContains(resp, 'MSISDN,First Name,Last Name,School,Region,Questions Completed,Percentage Correct')
        self.assertContains(resp, '+27123456789,,,school name,Test_Area,1,100')

        #csv + region that doesn't exist
        resp = c.get(reverse('reports.learner', kwargs={'mode': 1, 'region': 'Test_Area44'}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv', 'Test_Area44'))
        self.assertContains(resp, 'MSISDN,First Name,Last Name,School,Region,Questions Completed,Percentage Correct')
        self.assertNotContains(resp, '+27123456789')

    def test_report_learner_unique_area(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get(reverse('reports.unique_regions'))
        self.assertContains(resp, 'Test_Area')

    def test_admin_auth_app_changes(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get('/admin/auth/')
        self.assertContains(resp, 'User Permissions')

    def test_admin_report_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.question = self.create_test_question('q1', self.module)

        resp = c.get('/report_response/1000')
        self.assertContains(resp, 'Report 1000 not found')

        learner = self.create_learner(
            self.school,
            username="+27123456780",
            mobile="+27123456780",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        rep = Report.objects.create(
            user=learner,
            question=self.question,
            issue='e != mc^2',
            fix='e == 42',
            publish_date=datetime.now()
        )

        resp = c.get('/report_response/%s' % rep.id)
        self.assertContains(resp, 'Participant not found')

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 1, 18, 1, 1)
        )

        resp = c.get('/report_response/%s' % rep.id)
        self.assertContains(resp, 'Report Response')

        resp = c.post('/report_response/%s' % rep.id,
                      data={'title': '',
                            'publishdate_0': '',
                            'publishdate_1': '',
                            'content': ''
                            })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/report_response/%s' % rep.id,
                      data={'title': '',
                            'publishdate_0': '2015-33-33',
                            'publishdate_1': '99:99:99',
                            'content': ''
                            })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('/report_response/%s' % rep.id)
        self.assertContains(resp, 'This field is required.')

        rr_cnt = ReportResponse.objects.all().count()
        msg_cnt = Message.objects.all().count()

        resp = c.post('/report_response/%s' % rep.id,
                      data={'title': 'test',
                            'publishdate_0': '2014-01-01',
                            'publishdate_1': '00:00:00',
                            'content': '<p>Test</p>'
                            })

        self.assertEquals(ReportResponse.objects.all().count(), rr_cnt + 1)
        self.assertEquals(Message.objects.all().count(), msg_cnt + 1)

    def test_admin_msg_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        question = self.create_test_question('q5', self.module)

        resp = c.get('/message_response/1000')
        self.assertContains(resp, 'Message 1000 not found')

        learner = self.create_learner(
            self.school,
            username="+27223456780",
            mobile="+27223456780",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        msg = self.create_message(
            learner,
            self.course, name="msg",
            publishdate=datetime.now(),
            content='test message'
        )

        resp = c.get('/message_response/%s' % msg.id)
        self.assertContains(resp, 'Participant not found')

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 3, 18, 1, 1)
        )

        resp = c.get('/message_response/%s' % msg.id)
        self.assertContains(resp, 'Respond to Message')

        resp = c.post('/message_response/%s' % msg.id,
                      data={'title': '',
                            'publishdate_0': '',
                            'publishdate_1': '',
                            'content': ''
                            })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/message_response/%s' % msg.id,
                      data={'title': '',
                            'publishdate_0': '2015-33-33',
                            'publishdate_1': '99:99:99',
                            'content': ''
                            })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('/message_response/%s' % msg.id)
        self.assertContains(resp, 'This field is required.')

        msg_cnt = Message.objects.all().count()

        resp = c.post('/message_response/%s' % msg.id,
                      data={'title': 'test',
                            'publishdate_0': '2014-01-01',
                            'publishdate_1': '00:00:00',
                            'content': '<p>Test</p>'
                            })

        self.assertEquals(Message.objects.all().count(), msg_cnt + 1)
        msg = Message.objects.get(pk=msg.id)
        self.assertEquals(msg.responded, True)
        self.assertEquals(msg.responddate.date(), datetime.now().date())

    def test_admin_sms_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        resp = c.get('/sms_response/1000')
        self.assertContains(resp, 'Sms 1000 not found')

        learner = self.create_learner(
            self.school,
            username="+27223456781",
            mobile="+27223456781",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        sms = Sms.objects.create(
            uuid='123123123',
            message='test',
            msisdn=learner.mobile,
            date_sent=datetime.now()
        )

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 3, 18, 1, 1)
        )

        resp = c.get('/sms_response/%s' % sms.id)
        self.assertContains(resp, 'Respond to SMS')

        resp = c.post('/sms_response/%s' % sms.id,
                      data={'publishdate_0': '',
                            'publishdate_1': '',
                            'content': ''
                            })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/sms_response/%s' % sms.id,
                      data={'title': '',
                            'publishdate_0': '2015-33-33',
                            'publishdate_1': '99:99:99',
                            'content': ''
                            })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('/sms_response/%s' % sms.id)
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/sms_response/%s' % sms.id,
                      data={'publishdate_0': '2014-01-01',
                            'publishdate_1': '00:00:00',
                            'content': '<p>Test</p>'
                            })

        sms = Sms.objects.get(pk=sms.id)
        self.assertEquals(sms.responded, True)
        self.assertEquals(sms.respond_date.date(), datetime.now().date())
        self.assertIsNotNone(sms.response)

        qsms = SmsQueue.objects.get(msisdn=learner.mobile)
        self.assertEquals(qsms.message, '<p>Test</p>')

    def test_admin_discussion_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        question = self.create_test_question('q7', self.module)

        resp = c.get('/discussion_response/1000')
        self.assertContains(resp, 'Discussion 1000 not found')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456788",
            mobile="+27223456788",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        disc = Discussion.objects.create(
            name='Test',
            description='Test',
            content='Test content',
            author=learner,
            publishdate=datetime.now(),
            course=self.course,
            module=self.module,
            question=question
        )

        resp = c.get('/discussion_response/%s' % disc.id)
        self.assertContains(resp, 'Participant not found')

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 3, 18, 1, 1)
        )

        resp = c.get('/discussion_response/%s' % disc.id)
        self.assertContains(resp, 'Respond to Discussion')

        resp = c.post('/discussion_response/%s' % disc.id,
                      data={'title': '',
                            'publishdate_0': '',
                            'publishdate_1': '',
                            'content': ''
                            })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/discussion_response/%s' % disc.id,
                      data={'title': '',
                            'publishdate_0': '2015-33-33',
                            'publishdate_1': '99:99:99',
                            'content': ''
                            })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('/discussion_response/%s' % disc.id)
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/discussion_response/%s' % disc.id,
                      data={'title': 'test',
                            'publishdate_0': '2014-01-01',
                            'publishdate_1': '00:00:00',
                            'content': '<p>Test</p>'
                            })

        disc = Discussion.objects.get(pk=disc.id)
        self.assertIsNotNone(disc.response)
        self.assertEquals(disc.response.moderated, True)
        self.assertEquals(disc.response.author, self.admin_user)


@override_settings(VUMI_GO_FAKE=True)
class LearnerStateTest(TestCase):

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
        try:
            participant = Participant.objects.get(learner=learner)
        except Participant.DoesNotExist:
            participant = Participant.objects.create(
                learner=learner, classs=classs, **kwargs)

        return participant

    def create_test_question(self, name, module, **kwargs):
        return TestingQuestion.objects.create(name=name,
                                              module=module,
                                              **kwargs)

    def create_test_question_option(self, name, question):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=True)

    def create_test_answer(
            self,
            participant,
            question,
            option_selected,
            answerdate):
        return ParticipantQuestionAnswer.objects.create(
            participant=participant,
            question=question,
            option_selected=option_selected,
            answerdate=answerdate,
            correct=False
        )

    def create_and_answer_questions(self, num_questions, prefix, date):
        answers = []
        for x in range(0, num_questions):
            # Create a question
            question = self.create_test_question(
                'q' + prefix + str(x), self.module)

            question.save()
            option = self.create_test_question_option(
                'option_' + prefix + str(x),
                question)
            option.save()
            answer = self.create_test_answer(
                participant=self.participant,
                question=question,
                option_selected=option,
                answerdate=date
            )
            answer.save()
            answers.append(answer)

        return answers

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
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30))
        self.participant = self.create_participant(
            self.learner, self.classs, datejoined=datetime.now())
        self.module = self.create_module('module name', self.course)
        self.question = self.create_test_question('q1', self.module)
        self.option = self.create_test_question_option(
            'option_1',
            self.question)

        self.learner_state = LearnerState.objects.create(
            participant=self.participant,
            active_question=self.question
        )
        self.today = self.learner_state.today()

    @patch.object(LearnerState, 'today')
    def test_get_week_range(self, mock_get_today):
        # Today = Saturday the 23rd of August
        mock_get_today.return_value = datetime(2014, 8, 23, 0, 0, 0)
        week_range = self.learner_state.get_week_range()

        #Begin: Monday the 18th of August
        self.assertEquals(week_range[0], datetime(2014, 8, 18, 0, 0))

        #End: Friday the 22nd of August
        self.assertEquals(week_range[1], datetime(2014, 8, 23, 0, 0))

    def test_get_number_questions(self):
        # returns required - answered * questions per day(3)
        answered = 0
        number_questions = self.learner_state.get_number_questions(answered, 0)
        self.assertEquals(number_questions, 3)

        answered = 14
        number_questions = self.learner_state.get_number_questions(answered, 6)
        self.assertEquals(number_questions, 7)

    def test_is_weekend(self):
        day = 5  # Saturday
        self.assertTrue(self.learner_state.is_weekend(day))

        day = 2  # Wednesday
        self.assertFalse(self.learner_state.is_weekend(day))

    def test_get_all_answered(self):
        answer = ParticipantQuestionAnswer.objects.create(
            participant=self.participant,
            question=self.question,
            option_selected=self.option,
            answerdate=self.today - timedelta(days=1),
            correct=True
        )
        answer.save()
        answered = self.learner_state.get_all_answered().count()
        self.assertEquals(answered, 1)

    def test_get_training_questions(self):
        offset = (datetime.today().weekday() - 6) % 7
        last_saturday = datetime.today() - timedelta(days=offset)

        answer = ParticipantQuestionAnswer.objects.create(
            participant=self.participant,
            question=self.question,
            option_selected=self.option,
            answerdate=last_saturday,
            correct=True
        )
        answer.save()

        traing_questions = self.learner_state.get_training_questions()

        self.assertEquals(traing_questions.__len__(), 1)

    @patch.object(LearnerState, "today")
    def test_is_training_week(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 8, 27, 0, 0, 0)

        self.participant = self.create_participant(
            self.learner, self.classs,
            datejoined=datetime(2014, 8, 22, 0, 0, 0))

        self.learner_state = LearnerState.objects.create(
            participant=self.participant,
            active_question=self.question
        )

        self.assertTrue(self.learner_state.is_training_week())
        self.assertEquals(self.learner_state.get_questions_answered_week(), 0)

    def test_getnextquestion(self):
        active_question = self.learner_state.getnextquestion()

        self.assertEquals(active_question.name, 'q1')

    def test_get_today(self):
        self.assertEquals(get_today().date(), datetime.today().date())

    def test_get_unanswered_few_answered(self):
        # Create some more questions
        question2 = self.create_test_question("question2", self.module)
        question2_opt = self.create_test_question_option("qu2", question2)
        question3 = self.create_test_question("question3", self.module)
        question3_opt = self.create_test_question_option("qu3", question3)

        answer = ParticipantQuestionAnswer.objects.create(
            participant=self.participant,
            question=self.question,
            option_selected=self.option,
            answerdate=datetime.now(),
            correct=True
        )
        answer.save()

        self.assertListEqual(list(self.learner_state.get_unanswered()),
                             [question2, question3])

    def test_get_unanswered_many_modules(self):
        # Create modules belonging to course
        module2 = self.create_module("module2", self.course)

        # Create some more questions
        question2 = self.create_test_question("question2", self.module)
        question2_opt = self.create_test_question_option("qu2", question2)
        question3 = self.create_test_question("question3", module2)
        question3_opt = self.create_test_question_option("qu3", question3)

        answer = ParticipantQuestionAnswer.objects.create(
            participant=self.participant,
            question=self.question,
            option_selected=self.option,
            answerdate=datetime.now(),
            correct=True
        )
        answer.save()

        self.assertListEqual(list(self.learner_state.get_unanswered()),
                             [question2, question3])

    @patch.object(LearnerState, "today")
    def test_is_training_weekend(self, mock_get_today):
        self.participant = self.create_participant(
            self.learner, self.classs,
            datejoined=datetime(2014, 8, 22, 0, 0, 0))

        self.learner_state = LearnerState.objects.create(
            participant=self.participant,
            active_question=self.question
        )

        mock_get_today.return_value = datetime(2014, 8, 23, 0, 0, 0)

        # Create and answer 2 other questions earlier in the day
        answers = self.create_and_answer_questions(2, 'training',
                                                   datetime(2014, 8, 23,
                                                            1, 22, 0))
        training_questions = self.learner_state.get_training_questions()

        self.assertListEqual(training_questions, answers)
        self.assertEqual(
            self.learner_state.is_training_weekend(), True)
        self.assertEquals(self.learner_state.get_questions_answered_week(), 4)

    @patch.object(LearnerState, "today")
    def test_is_monday_after_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 8, 25, 0, 0, 0)
        self.assertTrue(self.learner_state.check_monday_after_training(1))
        self.assertFalse(self.learner_state.check_monday_after_training(
            self.learner_state.QUESTIONS_PER_DAY + 1))


class MockRequest(object):
    pass


class MockSuperUser(object):
    def has_perm(self, perm):
        return True


@override_settings(VUMI_GO_FAKE=True)
class OneplusAdminMetricTest(TestCase):

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

    def setUp(self):
        self.site = AdminSite()
        self.request = MockRequest()
        self.course = self.create_course()
        self.classs = self.create_class('class name', self.course)
        self.organisation = self.create_organisation()
        self.school = self.create_school('school name', self.organisation)
        self.learner = self.create_learner(
            self.school,
            username="+27123456789",
            mobile="+27123456789",
            country="country",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30))
