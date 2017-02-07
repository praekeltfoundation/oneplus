# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.utils import timezone

from django.db.models import Count, Sum
import logging
from auth.models import Learner, CustomUser
from communication.models import Message, Discussion, ChatGroup, ChatMessage, Profanity, Post, PostComment, \
    CoursePostRel, SmsQueue
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
from oneplus.views import get_week_day
from organisation.models import Course, Module, CourseModuleRel, Organisation, School
from oneplus.tasks import reset_learner_states
from communication.utils import contains_profanity


def append_query_params(url, params):
    if len(params) < 1:
        return url
    return '%s?%s' % (url, '&'.join([('%s=%s' % (idx, params[idx])) for idx in params.keys()]))


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
        if 'grade' not in kwargs:
            kwargs['grade'] = 'Grade 11'
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

    def create_event(self, name, course, activation_date, deactivation_date, **kwargs):
        return Event.objects.create(name=name, course=course, activation_date=activation_date,
                                    deactivation_date=deactivation_date, **kwargs)

    def create_sumit(self, name, course, activation_date, deactivation_date, **kwargs):
        return SUMit.objects.create(name=name, course=course, activation_date=activation_date,
                                    deactivation_date=deactivation_date, **kwargs)

    def create_event_start_page(self, event, header, paragraph):
        return EventStartPage.objects.create(event=event, header=header, paragraph=paragraph)

    def create_event_end_page(self, event, header, paragraph):
        return EventEndPage.objects.create(event=event, header=header, paragraph=paragraph)

    def create_event_splash_page(self, event, order_number, header, paragraph):
        return EventSplashPage.objects.create(event=event, order_number=order_number, header=header,
                                              paragraph=paragraph)

    def create_event_question(self, event, question, order):
        return EventQuestionRel.objects.create(event=event, question=question, order=order)

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
        self.create_test_question('question1', self.module, state=3)
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=None
        )

        # get next question
        learnerstate.getnextquestion()
        learnerstate.save()

        # check active question
        self.assertEquals(learnerstate.active_question.name, 'question1')

    def test_home(self):
        with patch("django.core.mail.mail_managers") as mock_mail_managers:
            self.client.get(reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
            )

            #no questions
            resp = self.client.get(reverse('learn.home'))
            self.assertEquals(resp.status_code, 200)

            #with questions
            self.create_test_question('question1', self.module, state=3)
            LearnerState.objects.create(
                participant=self.participant,
                active_question=None,
            )
            resp = self.client.get(reverse('learn.home'))
            self.assertEquals(resp.status_code, 200)

            #post with no event
            resp = self.client.post(reverse('learn.home'), data={"take_event": "event"}, follow=True)
            self.assertEquals(resp.status_code, 200)

            #with event active
            event_module = self.create_module("event_module", self.course, type=2)
            event = self.create_event("event_name", self.course, datetime.now() - timedelta(days=1),
                                      datetime.now() + timedelta(days=1), number_sittings=2, event_points=5, type=1)
            start_page = self.create_event_start_page(event, "Test Start Page", "Test Start Page Paragraph")
            end_page = self.create_event_end_page(event, "Test End Page", "Test Start Page Paragraph")
            question_1 = self.create_test_question("question_1", event_module, state=3)
            question_option_1 = self.create_test_question_option("question_1_option", question_1)
            self.create_event_question(event, question_1, 1)
            question_2 = self.create_test_question("question_2", event_module, state=3)
            question_option_2 = self.create_test_question_option("question_2_option", question_2)
            self.create_event_question(event, question_2, 2)

            resp = self.client.get(reverse('learn.home'))
            self.assertEquals(resp.status_code, 200)
            self.assertContains(resp, "Take the %s" % event.name)

            #no data in post
            resp = self.client.post(reverse('learn.home'), follow=True)
            self.assertEquals(resp.status_code, 200)

            #take event
            resp = self.client.post(reverse('learn.home'), data={"take_event": "event"}, follow=True)
            self.assertRedirects(resp, "event_start_page")
            self.assertContains(resp, start_page.header)

            #go to event_start_page
            resp = self.client.post(reverse("learn.event_start_page"),
                                    data={"event_start_button": "Get Started"}, follow=True)
            self.assertRedirects(resp, "event")

            #valid correct answer
            resp = self.client.post(reverse('learn.event'),
                                    data={'answer': question_option_1.id},
                                    follow=True)
            self.assertEquals(resp.status_code, 200)
            self.assertRedirects(resp, "event_right")

            resp = self.client.get(reverse('learn.home'))
            self.assertEquals(resp.status_code, 200)
            self.assertContains(resp, "Finish %s" % event.name)

            #take event the second time
            resp = self.client.post(reverse('learn.home'), data={"take_event": "event"}, follow=True)
            self.assertRedirects(resp, "event")

            #valid correct answer
            resp = self.client.post(reverse('learn.event'),
                                    data={'answer': question_option_2.id},
                                    follow=True)
            self.assertEquals(resp.status_code, 200)
            self.assertRedirects(resp, "event_right")

            resp = self.client.get(reverse('learn.event_end_page'))
            self.assertEquals(resp.status_code, 200)

            # resp = self.client.get(reverse('learn.home'))
            # self.assertContains(resp, "Points: <b>5</b>")

            for i in range(1, 15):
                question = TestingQuestion.objects.create(name="Question %d" % i, module=self.module)
                option = TestingQuestionOption.objects.create(name="Option %d.1" % i, question=question, correct=True)
                ParticipantQuestionAnswer.objects.create(participant=self.participant, question=question,
                                                         option_selected=option, correct=True)

            question = TestingQuestion.objects.create(name="Question %d" % 15, module=self.module)
            option = TestingQuestionOption.objects.create(name="Option %d.1" % 15, question=question, correct=False)
            ParticipantQuestionAnswer.objects.create(participant=self.participant, question=question,
                                                     option_selected=option, correct=False)

            Setting.objects.create(key="REPEATING_QUESTIONS_ACTIVE", value="true")

            resp = self.client.get(reverse('learn.home'))
            self.assertEquals(resp.status_code, 200)
            self.assertContains(resp, "Redo incorrect answers")

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
            publishdate=datetime.now(),
            moderated=True
        )

        resp = self.client.get(
            reverse('com.chat',
                    kwargs={'chatid': chatgroup.id})
        )
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'chatmsg1content')

        resp = self.client.post(
            reverse('com.chat',
                    kwargs={'chatid': chatgroup.id}),
            data={'comment': 'test'},
            follow=True
        )

        self.assertContains(resp, 'test')

        resp = self.client.post(
            reverse('com.chat',
                    kwargs={'chatid': chatgroup.id}),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('com.chat',
                    kwargs={'chatid': chatgroup.id}),
            data={'report': chatmsg1.id},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "This comment has been reported")

        Profanity.objects.create(
            word="crap"
        )

        resp = self.client.post(
            reverse('com.chat',
                    kwargs={'chatid': chatgroup.id}),
            data={'comment': 'crap'},
            follow=True
        )

        cm = ChatMessage.objects.all().last()
        self.assertEquals(cm.content, "This comment includes a banned word so has been removed.")
        self.assertEquals(cm.original_content, "crap")

    def test_blog(self):
        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': self.learner.unique_token})
        )

        blog = Post.objects.create(
            name='testblog',
            publishdate=datetime.now()
        )
        CoursePostRel.objects.create(course=self.course, post=blog)

        resp = self.client.get(
            reverse('com.blog',
                    kwargs={'blogid': blog.id})
        )
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('com.blog',
                    kwargs={'blogid': blog.id})
        )
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('com.blog',
                    kwargs={'blogid': blog.id}),
            data={'comment': 'New comment'},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Thank you for your contribution. Your message will display shortly!")

        pc = PostComment.objects.get(post=blog)
        self.assertEquals(pc.moderated, True)

        resp = self.client.post(
            reverse('com.blog',
                    kwargs={'blogid': blog.id}),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

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

    def test_reset_password(self):
        new_learner = self.create_learner(
            self.school,
            username="0701234567",
            mobile="0701234567")

        new_participant = self.create_participant(
            new_learner,
            self.classs,
            datejoined=datetime.now())

        resp = self.client.get(reverse('auth.reset_password', kwargs={'token': 'abc'}), follow=True)
        self.assertRedirects(resp, '/onboarding')

        new_learner.pass_reset_token = "abc"
        new_learner.pass_reset_token_expiry = datetime.now() + timedelta(days=1)
        new_learner.save()

        resp = self.client.get(reverse('auth.reset_password', kwargs={'token': '%s' % new_learner.pass_reset_token}))
        self.assertEquals(resp.status_code, 200)

        #invalid form
        resp = self.client.post(reverse('auth.reset_password', kwargs={'token': '%s' % new_learner.pass_reset_token}),
                                data={})
        self.assertContains(resp, "Please enter your new password")

        #passwords not matching
        resp = self.client.post(reverse('auth.reset_password', kwargs={'token': '%s' % new_learner.pass_reset_token}),
                                data={
                                    "password": '123',
                                    "password_2": '23'
                                })
        self.assertContains(resp, "Passwords do not match")

        password = "12345"
        resp = self.client.post(reverse('auth.reset_password', kwargs={'token': '%s' % new_learner.pass_reset_token}),
                                data={
                                    "password": password,
                                    "password_2": password
                                })
        self.assertContains(resp, "Password changed")

        resp = self.client.post(
            reverse('auth.login'),
            data={
                'username': new_learner.username,
                'password': password},
            follow=True
        )
        self.assertContains(resp, "WELCOME")

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

        self.assertEquals(learnerstate.get_total_questions(), 15)

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

        self.assertEquals(learnerstate.get_total_questions(), 15)

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
        self.assertEquals(learnerstate.get_total_questions(), 3)

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
        answered = list(learnerstate.get_answers_this_week().order_by("question"))

        self.assertListEqual(answered, answers)
        self.assertListEqual(learnerstate.get_week_range(), [monday.date(), tuesday.date()])

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
        self.assertEquals(learnerstate.get_total_questions(), 15)

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

        self.assertEquals(learnerstate.get_total_questions(), 15)
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

    def test_save_then_display2(self):
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
                                             question_content='test question', state=3)
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

    def test_badge_awarding(self):
        new_learner = self.create_learner(
            self.school,
            username="+27123456999",
            mobile="+2712345699",
            unique_token='xyz',
            unique_token_expiry=datetime.now() + timedelta(days=30))

        new_participant = self.create_participant(
            new_learner,
            self.classs,
            datejoined=datetime.now())

        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': new_learner.unique_token})
        )

        ten = 10
        gpb1 = self.create_gamification_point_bonus("Point Bonus", ten)

        # create the badges we want to win
        bt1 = self.create_badgetemplate(
            name="1st Correct",
            description="1st Correct"
        )

        bt2 = self.create_badgetemplate(
            name="15 Correct",
            description="15 Correct"
        )

        bt3 = self.create_badgetemplate(
            name="30 Correct",
            description="30 Correct"
        )

        bt4 = self.create_badgetemplate(
            name="100 Correct",
            description="100 Correct"
        )

        sc1 = self.create_gamification_scenario(
            name="1st correct",
            course=self.course,
            module=self.module,
            badge=bt1,
            event="1_CORRECT",
            point=gpb1
        )

        sc2 = self.create_gamification_scenario(
            name="15 correct",
            course=self.course,
            module=self.module,
            badge=bt2,
            event="15_CORRECT",
        )

        sc3 = self.create_gamification_scenario(
            name="30 correct",
            course=self.course,
            module=self.module,
            badge=bt3,
            event="30_CORRECT",
        )

        sc4 = self.create_gamification_scenario(
            name="100 correct",
            course=self.course,
            module=self.module,
            badge=bt4,
            event="100_CORRECT",
        )

        fifteen = 15
        for i in range(0, fifteen):
            question = self.create_test_question('q_15_%s' % i,
                                                 self.module,
                                                 question_content='test question',
                                                 state=3)

            question_option = self.create_test_question_option('q_15_%s_O_1' % i, question)

            self.client.get(reverse('learn.next'))
            self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        _total_correct = ParticipantQuestionAnswer.objects.filter(
            participant=new_participant,
            correct=True
        ).count()

        participant = Participant.objects.get(id=new_participant.id)
        self.assertEquals(participant.points, ten + fifteen)

        self.assertEquals(fifteen, _total_correct)

        thirty = 30
        for i in range(fifteen, thirty):
            question = self.create_test_question('q_30_%s' % i,
                                                 self.module,
                                                 question_content='test question',
                                                 state=3)

            question_option = self.create_test_question_option('q_30_%s_O_1' % i, question)

            self.client.get(reverse('learn.next'))
            self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        _total_correct = ParticipantQuestionAnswer.objects.filter(
            participant=new_participant,
            correct=True
        ).count()

        self.assertEquals(thirty, _total_correct)

        hundred = 100
        for i in range(thirty, hundred):
            question = self.create_test_question('q_100_%s' % i,
                                                 self.module,
                                                 question_content='test question',
                                                 state=3)

            question_option = self.create_test_question_option('q_100_%s_O_1' % i, question)

            self.client.get(reverse('learn.next'))
            self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        _total_correct = ParticipantQuestionAnswer.objects.filter(
            participant=new_participant,
            correct=True
        ).count()

        self.assertEquals(hundred, _total_correct)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt1,
            scenario=sc1
        ).count()
        self.assertEquals(cnt, 1)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt2,
            scenario=sc2
        ).count()
        self.assertEquals(cnt, 1)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt3,
            scenario=sc3
        ).count()
        self.assertEquals(cnt, 1)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt4,
            scenario=sc4
        ).count()
        self.assertEquals(cnt, 1)

    def test_badge_awarding_2(self):
        new_learner = self.create_learner(
            self.school,
            username="+27123456999",
            mobile="+2712345699",
            unique_token='xyz',
            unique_token_expiry=datetime.now() + timedelta(days=30))

        new_participant = self.create_participant(
            new_learner,
            self.classs,
            datejoined=datetime.now())

        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': new_learner.unique_token})
        )

        # create the badges we want to win
        bt1 = self.create_badgetemplate(
            name="15 Correct",
            description="15 Correct"
        )

        bt2 = self.create_badgetemplate(
            name="30 Correct",
            description="30 Correct"
        )

        bt3 = self.create_badgetemplate(
            name="100 Correct",
            description="100 Correct"
        )

        sc1 = self.create_gamification_scenario(
            name="15 correct",
            course=self.course,
            module=self.module,
            badge=bt1,
            event="15_CORRECT",
        )

        sc2 = self.create_gamification_scenario(
            name="30 correct",
            course=self.course,
            module=self.module,
            badge=bt2,
            event="30_CORRECT",
        )

        sc3 = self.create_gamification_scenario(
            name="100 correct",
            course=self.course,
            module=self.module,
            badge=bt3,
            event="100_CORRECT",
        )

        fifteen = 14
        for i in range(0, fifteen):
            question = self.create_test_question('q_15_%s' % i,
                                                 self.module,
                                                 question_content='test question',
                                                 state=3)

            question_option = self.create_test_question_option('q_15_%s_O_1' % i, question)

            new_participant.answer(question, question_option)

        question = self.create_test_question('q_15_16',
                                             self.module,
                                             question_content='test question',
                                             state=3)

        question_option = self.create_test_question_option('q_15_16_O_1', question)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt1,
            scenario=sc1
        ).count()
        self.assertEquals(cnt, 0)

        self.client.get(reverse('learn.next'))
        self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt1,
            scenario=sc1
        ).count()
        self.assertEquals(cnt, 1)

        thirty = 29
        for i in range(fifteen + 1, thirty):
            question = self.create_test_question('q_30_%s' % i,
                                                 self.module,
                                                 question_content='test question',
                                                 state=3)

            question_option = self.create_test_question_option('q_30_%s_O_1' % i, question)

            new_participant.answer(question, question_option)

        question = self.create_test_question('q_30_31',
                                             self.module,
                                             question_content='test question',
                                             state=3)

        question_option = self.create_test_question_option('q_30_31_O_1', question)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt2,
            scenario=sc2
        ).count()
        self.assertEquals(cnt, 0)

        self.client.get(reverse('learn.next'))
        self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt2,
            scenario=sc2
        ).count()
        self.assertEquals(cnt, 1)

        hundred = 99
        for i in range(thirty + 1, hundred):
            question = self.create_test_question('q_100_%s' % i,
                                                 self.module,
                                                 question_content='test question',
                                                 state=3)

            question_option = self.create_test_question_option('q_100_%s_O_1' % i, question)

            new_participant.answer(question, question_option)

        question = self.create_test_question('q_100_101',
                                             self.module,
                                             question_content='test question',
                                             state=3)

        question_option = self.create_test_question_option('q_100_101_O_1', question)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt3,
            scenario=sc3
        ).count()
        self.assertEquals(cnt, 0)

        self.client.get(reverse('learn.next'))
        self.client.post(reverse('learn.next'), data={'answer': question_option.id}, follow=True)

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt3,
            scenario=sc3
        ).count()
        self.assertEquals(cnt, 1)

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

        self.assertContains(resp, "Well done")

        # Post empty
        resp = c.post(
            reverse('learn.preview', kwargs={'questionid': self.question.id}),
            data={}, follow=True
        )
        self.assertEquals(resp.status_code, 200)

        # Post a incorrect answer
        option = self.create_test_question_option("wrong", self.question, False)
        resp = c.post(
            reverse('learn.preview', kwargs={'questionid': self.question.id}),
            data={'answer': option.id}, follow=True
        )

        self.assertContains(resp, "Next time")

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

        self.assertContains(resp, "Well done")

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
            question_content='test question',
            state=3)

        self.questionoption = self.create_test_question_option(
            'questionoption1',
            self.question)

        resp = c.get(
            reverse(
                'learn.preview.wrong',
                kwargs={
                    'questionid': self.question.id}))

        self.assertContains(resp, "Next time")

    def test_wrong_view(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        question = self.create_test_question(
            'question1', self.module,
            question_content='test question',
            state=3)

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
        self.assertContains(resp, "Next time")

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

        resp = self.client.post(
            reverse("misc.contact"),
            follow=True,
            data={
                "fname": "Test",
                "sname": "test",
                "contact": "0123456789",
                "comment": "test",
                "school": "Test School",
                "grade": "11",
            }
        )

        self.assertContains(resp, "Your message has been sent. We will get back to you in the next 24 hours")

    def test_contact_screen_with_failure_and_bad_data(self):
        with patch("oneplus.misc_views.mail_managers") as mock_mail_managers:
            mock_mail_managers.side_effect = KeyError('e')

            resp = self.client.post(
                reverse("misc.contact"),
                follow=True,
                data={
                    "fname": "Test",
                    "sname": "test",
                    "contact": "0123456789\n0123456789\n0123456789",
                    "comment": "test",
                    "school": "Test School",
                    "grade": "11"
                }
            )

            self.assertContains(resp, "Your message has been sent. We will get back to you in the next 24 hours")
            mock_mail_managers.assert_called()

    def test_get_week_day(self):
        day = get_week_day()
        self.assertLess(day, 7)
        self.assertGreaterEqual(day, 0)

    def test_menu_screen(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        #create event_session variable
        s = self.client.session
        s["event_session"] = True
        s.save()

        resp = self.client.get(reverse('core.menu'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('core.menu'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_login(self):
        resp = self.client.get(reverse('auth.login'))
        self.assertEquals(resp.status_code, 200)

        c = Client()

        resp = c.post(
            reverse('auth.login'),
            data={},
            follow=True
        )

        self.assertContains(resp, "Sign in")

        password = 'mypassword'
        my_admin = CustomUser.objects.create_superuser(
            username='asdf',
            email='asdf@example.com',
            password=password,
            mobile='+27111111111')

        c.login(username=my_admin.username, password=password)

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27198765432",
                'password': password},
            follow=True
        )

        self.assertContains(resp, "dig-it is currently in test phase")

        learner = Learner.objects.create_user(
            username="+27231231231",
            mobile="+27231231231",
            grade='Grade 11',
            password='1234'
        )
        learner.save()

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )

        self.assertContains(resp, "You are not currently linked to a class")

        learner.is_active = False
        learner.save()

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )
        self.assertContains(resp, "GET CONNECTED")

        learner.is_active = True
        learner.save()

        self.create_participant(
            learner,
            self.classs,
            datejoined=datetime.now())

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1235'},
            follow=True
        )

        self.assertContains(resp, "incorrect password")

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )

        self.assertContains(resp, "WELCOME")

        question1 = self.create_test_question(
            'question1',
            self.module,
            question_content='test question'
        )
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

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )

        self.assertContains(resp, "WELCOME")

        self.create_participant(
            learner,
            self.classs,
            datejoined=datetime.now()
        )

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )
        self.assertContains(resp, "Account Issue")

    def test_getconnected(self):
        resp = self.client.post(
            reverse('auth.getconnected')
        )
        self.assertContains(resp, "GET CONNECTED")

        learner = Learner.objects.create_user(
            username="+27891234567",
            mobile="+27891234567",
            password='1234'
        )
        self.create_participant(
            learner,
            self.classs,
            datejoined=datetime.now()
        )
        self.client.post(
            reverse('auth.login'),
            data={
                'username': "+27891234567",
                'password': '1234'},
            follow=True
        )

        resp = self.client.post(
            reverse('auth.getconnected')
        )
        self.assertContains(resp, "GET CONNECTED")

    def test_points_screen(self):
        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('prog.points'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.points'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_leaderboard_screen(self):
        question_list = list()
        question_option_list = list()
        question_option_wrong_list = list()

        for x in range(0, 11):
            question = self.create_test_question('question_%s' % x,
                                                 self.module,
                                                 question_content='test question',
                                                 state=3)
            question_option = self.create_test_question_option('question_option_%s' % x, question)
            question_wrong_option = self.create_test_question_option('question_option_w_%s' % x, question, False)

            question_list.append(question)
            question_option_list.append(question_option)
            question_option_wrong_list.append(question_wrong_option)

        all_learners_classes = []
        all_particpants_classes = []
        all_learners = []
        all_particpants = []
        counter = 0
        password = "12345"

        test_class = self.create_class('test_class', self.course)

        for x in range(10, 21):
            all_learners.append(self.create_learner(self.school,
                                                    first_name="test_%s" % x,
                                                    username="07612345%s" % x,
                                                    mobile="07612345%s" % x,
                                                    unique_token='%s' % x,
                                                    unique_token_expiry=datetime.now() + timedelta(days=30)))
            all_learners[counter].set_password(password)

            all_particpants.append(self.create_participant(all_learners[counter],
                                                           test_class, datejoined=datetime.now()))

            for y in range(0, counter+1):
                all_particpants[y].answer(question_list[y], question_option_list[y])
                all_particpants[y].answer(question_list[y], question_option_list[y])

            #data for class leaderboard
            new_class = self.create_class('class_%s' % x, self.course)
            all_learners_classes.append(self.create_learner(self.school,
                                                            first_name="test_b_%s" % x,
                                                            username="08612345%s" % x,
                                                            mobile="08612345%s" % x,
                                                            unique_token='abc%s' % x,
                                                            unique_token_expiry=datetime.now() + timedelta(days=30)))
            all_learners_classes[counter].set_password(password)

            all_particpants_classes.append(self.create_participant(all_learners_classes[counter],
                                                                   new_class, datejoined=datetime.now()))

            for y in range(0, counter+1):
                all_particpants_classes[y].answer(question_list[y], question_option_wrong_list[y])

            all_particpants_classes[counter].answer(question_list[counter], question_option_list[counter])
            all_particpants_classes[counter].answer(question_list[counter], question_option_list[counter])
            all_particpants_classes[counter].answer(question_list[counter], question_option_wrong_list[counter])
            all_particpants_classes[counter].answer(question_list[counter], question_option_wrong_list[counter])

            counter += 1

        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': "20"})
        )

        resp = self.client.get(reverse('prog.leader'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.leader'), follow=True)
        self.assertEquals(resp.status_code, 200)

        # overall leaderboard is overall in class, not over all classes
        resp = self.client.get(reverse('prog.leader'), follow=True)

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_20")
        self.assertContains(resp, "11th place")
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")
        self.assertContains(resp, "Show more", count=3)

        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': "14"})
        )

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_14")
        self.assertContains(resp, "5<sup>th</sup> place")
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")
        self.assertContains(resp, "Show more", count=3)

    def test_leaderboard_collapse(self):
        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")
        self.assertContains(resp, "Show more", count=3)

        resp = self.client.post(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")
        self.assertContains(resp, "Show more", count=3)

        resp = self.client.post(reverse('prog.leader'), data={'board.class.active': 'true'}, follow=True)
        self.assertContains(resp, "Show more", count=2)
        self.assertContains(resp, "Show less", count=1)

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Show more", count=2)
        self.assertContains(resp, "Show less", count=1)

        resp = self.client.post(reverse('prog.leader'),
                                data={
                                    'board.class.active': 'true',
                                    'board.school.active': 'true',
                                    'board.national.active': 'true'},
                                follow=True)
        self.assertContains(resp, "Show more", count=0)
        self.assertContains(resp, "Show less", count=3)

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Show more", count=0)
        self.assertContains(resp, "Show less", count=3)

        resp = self.client.post(reverse('prog.leader'),
                                data={
                                    'board.class.active': 'false',
                                    'board.school.active': 'false',
                                    'board.national.active': 'false'},
                                follow=True)
        self.assertContains(resp, "Show more", count=3)
        self.assertContains(resp, "Show less", count=0)

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Show more", count=3)
        self.assertContains(resp, "Show less", count=0)

    def test_leaderboard_with_almost_no_results(self):
        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "1<sup>st</sup> place", count=3)
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")

    def test_leaderboard_school_multiple_entrants(self):
        school = self.create_school('Some Random School', self.organisation)
        learner1 = self.create_learner(school,
                                       first_name="learner_1",
                                       grade="Grade 11",
                                       mobile="1111111111",
                                       unique_token='blargity',
                                       unique_token_expiry=datetime.now() + timedelta(days=30),
                                       username="1111111111")
        learner2 = self.create_learner(school,
                                       first_name="learner_2",
                                       grade="Grade 11",
                                       mobile="2222222222",
                                       username="2222222222")
        learner3 = self.create_learner(school,
                                       first_name="learner_3",
                                       grade="Grade 11",
                                       mobile="3333333333",
                                       username="3333333333")

        participant1 = self.create_participant(learner1,
                                               self.classs,
                                               datejoined=timezone.now(),
                                               is_active=True,
                                               points=5)
        particpiant2 = self.create_participant(learner2,
                                               self.classs,
                                               datejoined=timezone.now(),
                                               is_active=True,
                                               points=10)
        particpiant3 = self.create_participant(learner3,
                                               self.classs,
                                               datejoined=timezone.now(),
                                               is_active=True,
                                               points=15)

        self.school.name = 'First School'
        self.school.save()
        self.learner.grade = 'Grade 11'
        self.learner.save()
        self.participant.points = 1
        self.participant.save()

        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': learner1.unique_token})
        )
        resp = self.client.post(reverse('prog.leader'), data={'board.school.active': 'true'}, follow=True)

        self.assertContains(resp, school.name, count=1)
        self.assertContains(resp, self.school.name, count=1)

    def test_ontrack_screen(self):
        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('prog.ontrack'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.ontrack'), follow=True)
        self.assertEquals(resp.status_code, 200)

        #more than 10 answered
        self.create_and_answer_questions(11, "name", datetime.now())
        resp = self.client.get(reverse('prog.ontrack'))
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

        resp = self.client.post(
            reverse('com.bloglist'),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

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
        self.assertContains(resp, 'DIG-IT')

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
        # csv no region
        resp = c.get(reverse('reports.learner', kwargs={'mode': 1, 'region': ''}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv'))

        # xls no region
        resp = c.get(reverse('reports.learner', kwargs={'mode': 2, 'region': ''}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('xls'))

        # csv + region
        resp = c.get(reverse('reports.learner', kwargs={'mode': 1, 'region': 'Test_Area'}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv', 'Test_Area'))
        self.assertContains(resp, 'MSISDN,First Name,Last Name,School,Region,Class,Questions Completed,'
                                  'Percentage Correct')
        self.assertContains(resp, '+27123456789,,,school name,Test_Area,class name,1,100')

        # csv + region that doesn't exist
        resp = c.get(reverse('reports.learner', kwargs={'mode': 1, 'region': 'Test_Area44'}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv', 'Test_Area44'))
        self.assertContains(resp, 'MSISDN,First Name,Last Name,School,Region,Class,Questions Completed,'
                                  'Percentage Correct')
        self.assertNotContains(resp, '+27123456789')

        # wrong mode
        resp = c.get(reverse("reports.learner", kwargs={"mode": 3, "region": ""}))
        self.assertEquals(resp.get("Content-Type"), "text/html; charset=utf-8")
        self.assertEquals(resp.get("location"), "http://testserver/reports")
        self.assertEquals(resp.status_code, 302)

    def test_report_learner_unique_area(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get(reverse('reports.unique_regions'))
        self.assertContains(resp, 'Test_Area')

    def test_sumit_report(self):
        learner = self.create_learner(self.school, first_name='John', last_name='Smit', mobile='0791234567',
                                      unique_token='qwerty',
                                      unique_token_expiry=datetime.now() + timedelta(days=30))
        course = self.create_course('Maths Course')
        module = self.create_module('Maths Module', course, type=Module.EVENT)
        classs = self.create_class('A class', course)
        participant = self.create_participant(learner, classs, datejoined=datetime.now())
        sumit = self.create_sumit('First Summit', course, datetime.now(), datetime.now() + timedelta(days=2))

        question_option_set = list()
        for i in range(1, 16):
            question = self.create_test_question('easy_question_%2d' % i, module, difficulty=TestingQuestion.DIFF_EASY,
                                                 state=TestingQuestion.PUBLISHED)
            correct_option = self.create_test_question_option('easy_question_%2d_o_1' % i, question)
            question_option_set.append((question, correct_option))
            EventQuestionRel.objects.create(order=i, event=sumit, question=question)

        for i in range(16, 27):
            question = self.create_test_question('normal_question_%2d' % i, module,
                                                 difficulty=TestingQuestion.DIFF_NORMAL,
                                                 state=TestingQuestion.PUBLISHED)
            correct_option = self.create_test_question_option('normal_question_%2d_o_1' % i, question)
            question_option_set.append((question, correct_option))
            EventQuestionRel.objects.create(order=i-15, event=sumit, question=question)

        for i in range(27, 32):
            question = self.create_test_question('advanced_question_%2d' % i, module,
                                                 difficulty=TestingQuestion.DIFF_ADVANCED,
                                                 state=TestingQuestion.PUBLISHED)
            correct_option = self.create_test_question_option('advanced_question_%2d_o_1' % i, question)
            question_option_set.append((question, correct_option))
            EventQuestionRel.objects.create(order=i-26, event=sumit, question=question)

        for i in range(0, 4):
            EventQuestionAnswer.objects.create(event=sumit, participant=participant,
                                               question=question_option_set[i][0],
                                               question_option=question_option_set[i][1],
                                               correct=True)

        for i in range(15, 21):
            EventQuestionAnswer.objects.create(event=sumit, participant=participant,
                                               question=question_option_set[i][0],
                                               question_option=question_option_set[i][1],
                                               correct=True)

        for i in range(26, 31):
            EventQuestionAnswer.objects.create(event=sumit, participant=participant,
                                               question=question_option_set[i][0],
                                               question_option=question_option_set[i][1],
                                               correct=True)

        LearnerState.objects.create(participant=participant, sumit_level=5)
        EventParticipantRel.objects.create(event=sumit, participant=participant, sitting_number=1,
                                           results_received=False)

        sumit_level_name = SUMitLevel.objects.get(order=5).name

        self.client.get(reverse('auth.autologin', kwargs={'token': learner.unique_token}))
        self.client.get(reverse('learn.sumit_end_page'))

        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get(reverse('report.sumit', kwargs={"mode": 1, "sumit_id": "%d" % sumit.id}))
        self.assertContains(resp, learner.first_name)
        self.assertContains(resp, learner.last_name)
        self.assertContains(resp, learner.mobile)
        self.assertContains(resp, "Yes", 2)
        self.assertContains(resp, sumit_level_name)

        resp = c.get(reverse('report.sumit', kwargs={"mode": 2, "sumit_id": "%d" % sumit.id}))
        self.assertEquals(resp.status_code, 200)

        #not a winner
        LearnerState.objects.filter(participant=participant).delete()
        EventParticipantRel.objects.filter(event=sumit, participant=participant).delete()

        LearnerState.objects.create(participant=participant, sumit_level=5)
        EventParticipantRel.objects.create(event=sumit, participant=participant, sitting_number=1,
                                           results_received=False)

        ans = EventQuestionAnswer.objects.filter(participant=participant, event=sumit).order_by('answer_date').last()
        ans.correct = False
        ans.save()

        self.client.get(reverse('auth.autologin', kwargs={'token': learner.unique_token}))
        self.client.get(reverse('learn.sumit_end_page'))

        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get(reverse('report.sumit', kwargs={"mode": 1, "sumit_id": "%d" % sumit.id}))
        self.assertContains(resp, learner.first_name)
        self.assertContains(resp, learner.last_name)
        self.assertContains(resp, learner.mobile)
        self.assertContains(resp, "Yes", 1)
        self.assertContains(resp, "John,No", 1)
        self.assertContains(resp, sumit_level_name)

       #Sumit not complete
        LearnerState.objects.filter(participant=participant).delete()
        EventParticipantRel.objects.filter(event=sumit, participant=participant).delete()

        LearnerState.objects.create(participant=participant, sumit_level=5)
        EventParticipantRel.objects.create(event=sumit, participant=participant, sitting_number=1,
                                           results_received=False)

        EventQuestionAnswer.objects.filter(participant=participant, event=sumit).order_by('answer_date').last().delete()
        self.client.get(reverse('auth.autologin', kwargs={'token': learner.unique_token}))
        self.client.get(reverse('learn.sumit_end_page'))

        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get(reverse('report.sumit', kwargs={"mode": 1, "sumit_id": "%d" % sumit.id}))
        self.assertContains(resp, learner.first_name)
        self.assertContains(resp, learner.last_name)
        self.assertContains(resp, learner.mobile)
        self.assertNotContains(resp, "Yes")
        self.assertContains(resp, "John,No", 1)
        self.assertContains(resp, "14,No", 1)
        self.assertNotContains(resp, sumit_level_name)

        # Invalid Calls
        resp = c.get(reverse('report.sumit', kwargs={"mode": 3, "sumit_id": "%d" % sumit.id}))
        self.assertRedirects(resp, "reports")

        resp = c.get(reverse('report.sumit', kwargs={"mode": 1, "sumit_id": "%d" % 9999}))
        self.assertRedirects(resp, "reports")

    def test_sumit_report_list(self):
        sumit = self.create_sumit('First Summit', self.course, datetime.now(), datetime.now() + timedelta(days=2))
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get(reverse('report.sumit_list'))
        self.assertContains(resp, sumit.name)

    def test_admin_auth_app_changes(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        resp = c.get('/admin/auth/')
        self.assertContains(resp, 'User Permissions')

    def test_get_courses(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        resp = c.get('/courses')
        self.assertContains(resp, '"name": "course name"')

    def test_get_classes(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.create_class(name='test class 42', course=self.course)

        resp = c.get('/classes/all')
        self.assertContains(resp, '"name": "class name"')
        self.assertContains(resp, '"name": "test class 42"')

        resp = c.get('/classes/%s' % self.course.id)
        self.assertContains(resp, '"name": "class name"')

        resp = c.get('/classes/abc')
        self.assertEquals(resp.status_code, 200)

        resp = c.get('/classes/%s' % 999)
        self.assertEquals(resp.status_code, 200)

    def test_space_available(self):
        maximum = int(Setting.objects.get(key="MAX_NUMBER_OF_LEARNERS").value)
        total_reg = Participant.objects.aggregate(registered=Count('id'))
        available = maximum - total_reg.get('registered')

        learner = self.create_learner(
            self.school,
            username="+27123456999",
            mobile="+2712345699", )

        self.participant = self.create_participant(
            learner,
            self.classs,
            datejoined=datetime.now())
        available -= 1

        space, number_spaces = space_available()
        self.assertEquals(space, True)
        self.assertEquals(number_spaces, available)

        learner2 = self.learner = self.create_learner(
            self.school,
            username="+27123456988",
            mobile="+2712345688")

        self.participant = self.create_participant(
            learner2,
            self.classs,
            datejoined=datetime.now())
        available -= 1

        space, number_spaces = space_available()

        self.assertEquals(space, True)
        self.assertEquals(number_spaces, available)

    def test_signup(self):
        learner = self.create_learner(
            self.school,
            username="+27123456999",
            mobile="+2712345699", )

        self.participant = self.create_participant(
            learner,
            self.classs,
            datejoined=datetime.now())

        resp = self.client.get(reverse('auth.signup'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('auth.signup'), data={'yes': "Yes, please sign me up!"}, follow=True)
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('auth.signup'), data={'no': "Not interested right now"}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>DIG-IT | HELLO</title>")

    def test_signup_form(self):
        with patch("oneplus.auth_views.mail_managers") as mock_mail_managers:
            province_school = School.objects.get(name="Open School")
            self.course.name = settings.GRADE_10_COURSE_NAME
            self.course.save()
            promaths_school = self.create_school("ProMaths School",
                                                 province_school.organisation,
                                                 open_type=School.OT_CLOSED)
            promaths_class = self.create_class("ProMaths Class",
                                               self.course)
            resp = self.client.get(reverse('auth.signup_form'))
            self.assertEqual(resp.status_code, 200)

            # no data given
            resp = self.client.post(reverse('auth.signup_form'),
                                    data={},
                                    follow=True)
            self.assertContains(resp, "This must be completed", count=3)

            # invalid cellphone, grade and province
            resp = self.client.post(reverse('auth.signup_form'),
                                    data={
                                        'first_name': self.learner.first_name,
                                        'surname': self.learner.last_name,
                                        'cellphone': '12345',
                                        'enrolled': 0,
                                    },
                                    follow=True)
            self.assertContains(resp, "Enter a valid cellphone number")

            # registered cellphone
            resp = self.client.post(reverse('auth.signup_form'),
                                    data={
                                        'first_name': "Bob",
                                        'surname': "Bobby",
                                        'cellphone': self.learner.mobile,
                                        'grade': 'Grade 10',
                                        'province': 'Gauteng',
                                        'enrolled': 0
                                    },
                                    follow=True)
            self.assertContains(resp, "This number has already been registered.")

            # valid - enrolled
            resp = self.client.post(reverse('auth.signup_form'),
                                    data={
                                        'first_name': "Bob",
                                        'surname': "Bobby",
                                        'cellphone': '0729876543',
                                        'province': 'Gauteng',
                                        'grade': 'Grade 10',
                                        'enrolled': 0,
                                    },
                                    follow=True)
            self.assertContains(resp, 'Bob')
            self.assertContains(resp, 'Bobby')
            self.assertContains(resp, '0729876543')
            self.assertContains(resp, 'Gauteng')
            self.assertContains(resp, 'Grade 10')
            self.assertContains(resp, '0')

            #get request
            resp = self.client.get(reverse('auth.signup_form_normal'), follow=True)
            self.assertContains(resp, "Register")

            #no data
            resp = self.client.post(reverse('auth.signup_form_normal'), follow=True)
            self.assertContains(resp, "Register")

            with patch("oneplus.auth_views.SearchQuerySet") as MockSearchSet:
                # non-empty search result
                MockSearchSet().filter().values.return_value = [{'pk': 1, 'name': 'Blargity School'}]
                resp = self.client.post(reverse('auth.signup_form_normal'),
                                        data={
                                            'first_name': "Bob",
                                            'surname': "Bobby",
                                            'cellphone': '0729876543',
                                            'province': 'Gauteng',
                                            'grade': 'Grade 10',
                                            'enrolled': 1,
                                            'school_dirty': 'blarg'},
                                        follow=True)
                MockSearchSet.assert_called()
                self.assertContains(resp, 'Blargity School')
                MockSearchSet.clear()

                # No search results
                MockSearchSet().filter().values.return_value = []
                resp = self.client.post(reverse('auth.signup_form_normal'),
                                        data={
                                            'first_name': "Bob",
                                            'surname': "Bobby",
                                            'cellphone': '0729876543',
                                            'province': 'Gauteng',
                                            'grade': 'Grade 10',
                                            'enrolled': 1,
                                            'school_dirty': 'blarg'},
                                        follow=True)
                MockSearchSet.assert_called()
                self.assertContains(resp, 'No schools were a close enough match')
                MockSearchSet.clear()

                # Failed ElasticSearch
                MockSearchSet().filter().values.side_effect = Exception('LOL! ERROR.')
                resp = self.client.post(reverse('auth.signup_form_normal'),
                                        data={
                                            'first_name': "Bob",
                                            'surname': "Bobby",
                                            'cellphone': '0729876543',
                                            'province': 'Gauteng',
                                            'grade': 'Grade 10',
                                            'enrolled': 1,
                                            'school_dirty': self.school.name},
                                        follow=True)
                MockSearchSet.assert_called()
                self.assertContains(resp, 'No schools were a close enough match')
                MockSearchSet.clear()

            #invalid school and class
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Bob",
                                        'surname': "Bobby",
                                        'cellphone': '0729876543',
                                        'province': 'Gauteng',
                                        'grade': 'Grade 10',
                                        'enrolled': 1,
                                        'school': 999
                                    },
                                    follow=True)
            self.assertContains(resp, "No such school exists")

            #valid data
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Bob",
                                        'surname': "Bobby",
                                        'cellphone': '0729876543',
                                        'province': 'Gauteng',
                                        'grade': 'Grade 10',
                                        'enrolled': 0,
                                        'school': promaths_school.id
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876543')
            self.assertEquals('Bob', new_learner.first_name)

            # valid - not enrolled - grade 10 - no open class created
            self.school.province = "Gauteng"
            self.school.save()
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Koos",
                                        'surname': "Botha",
                                        'cellphone': '0729876540',
                                        'grade': 'Grade 10',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876540')
            self.assertEquals('Koos', new_learner.first_name)

            try:
                School.objects.get(name=settings.OPEN_SCHOOL).delete()
            except School.DoesNotExist:
                pass

            # valid - not enrolled - grade 10
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Willy",
                                        'surname': "Wolly",
                                        'cellphone': '0729878963',
                                        'grade': 'Grade 10',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729878963')
            self.assertEquals('Willy', new_learner.first_name)

            self.course.name = settings.GRADE_11_COURSE_NAME
            self.course.save()

            # valid - not enrolled - grade 11 - creaing open class
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Tom",
                                        'surname': "Tom",
                                        'cellphone': '0729876576',
                                        'grade': 'Grade 11',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876576')
            self.assertEquals('Tom', new_learner.first_name)

            # valid - not enrolled - grade 11
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Henky",
                                        'surname': "Tanky",
                                        'cellphone': '0729876486',
                                        'grade': 'Grade 11',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876486')
            self.assertEquals('Henky', new_learner.first_name)

            resp = self.client.get(reverse("auth.signup_form_normal"))
            self.assertContains(resp, 'Let\'s sign you up')

            self.course.name = settings.GRADE_12_COURSE_NAME
            self.course.save()

            # valid - not enrolled - grade 12 - creaing open class
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Rob",
                                        'surname': "Web",
                                        'cellphone': '0729876599',
                                        'grade': 'Grade 12',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876599')
            self.assertEquals('Rob', new_learner.first_name)

            # valid - not enrolled - grade 12
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Kyle",
                                        'surname': "Evans",
                                        'cellphone': '0729876444',
                                        'grade': 'Grade 12',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876444')
            self.assertEquals('Kyle', new_learner.first_name)

            resp = self.client.get(reverse("auth.signup_form_normal"))
            self.assertContains(resp, 'Let\'s sign you up')

    # @override_settings(GRADE_11_COURSE_NAME='Grade 11 Course')
    def test_signup_return(self):
        with patch("oneplus.auth_views.mail_managers") as mock_mail_managers:
            # test not logged in
            resp = self.client.get(reverse('auth.return_signup'))
            self.assertRedirects(resp, reverse('auth.login'))
            resp = self.client.get(reverse('auth.return_signup_school_confirm'))
            self.assertRedirects(resp, reverse('auth.login'))

            # test user not enrolled
            self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
            resp = self.client.get(reverse('auth.return_signup'))
            self.assertRedirects(resp, reverse('learn.home'))
            resp = self.client.get(reverse('auth.return_signup_school_confirm'))
            self.assertRedirects(resp, reverse('learn.home'))

            self.learner.first_name = 'Blarg'
            self.learner.last_name = 'Honk'
            self.learner.enrolled = '0'
            self.learner.save()

            self.course.name = settings.GRADE_11_COURSE_NAME
            self.course.save()

            resp = self.client.get(reverse('learn.home'), folow=True)
            self.assertRedirects(resp, reverse('auth.return_signup'))

            # plain get
            resp = self.client.get(reverse('auth.return_signup'), folow=True)
            self.assertContains(resp, 'Hello, %s.' % self.learner.first_name, count=1)

            # no data given
            resp = self.client.post(reverse('auth.return_signup'),
                                    data={},
                                    follow=True)
            self.assertContains(resp, "This must be completed", count=3)
            self.assertContains(resp, 'Hello, %s' % self.learner.first_name, count=1)

            # correct data given (p1)
            resp = self.client.post(reverse('auth.return_signup'),
                                    data={
                                        'grade': 'Grade 11',
                                        'province': 'Gauteng',
                                        'school_dirty': self.school.name},
                                    follow=True)
            self.assertContains(resp, self.school.name)

            # test ElasticSearch succeeds
            with patch("oneplus.auth_views.SearchQuerySet") as MockSearchSet:
                # non-empty search result
                MockSearchSet().filter().values.return_value = [{'pk': 1, 'name': 'Blargity School'}]
                resp = self.client.post(reverse('auth.return_signup'),
                                        data={
                                            'province': 'Gauteng',
                                            'grade': 'Grade 11',
                                            'school_dirty': 'blarg'},
                                        follow=True)
                MockSearchSet.assert_called()
                self.assertContains(resp, 'Blargity School')
                MockSearchSet.clear()

            # get redirect (p2)
            resp = self.client.get(reverse('auth.return_signup_school_confirm'), follow=True)
            self.assertRedirects(resp, reverse('auth.return_signup'))
            self.assertContains(resp, 'Hello, %s' % self.learner.first_name, count=1)

            # incomplete data given (p2)
            resp = self.client.post(reverse('auth.return_signup_school_confirm'),
                                    data={},
                                    follow=True)
            self.assertContains(resp, "This must be completed", count=3)

            # incorrect data given (p2)
            resp = self.client.post(reverse('auth.return_signup_school_confirm'),
                                    data={
                                        'grade': 'Grade 11',
                                        'province': 'Gauteng',
                                        'school': 'other'},
                                    follow=True)
            self.assertContains(resp, 'No such school')

            # correct data given (p2)
            resp = self.client.post(reverse('auth.return_signup_school_confirm'),
                                    data={
                                        'grade': 'Grade 11',
                                        'province': 'Gauteng',
                                        'school': self.school.id},
                                    follow=True)
            self.assertRedirects(resp, reverse('learn.home'))
            self.participant = Participant.objects.get(pk=self.participant.pk)
            self.assertFalse(self.participant.is_active)
            self.assertNotEqual(Participant.objects.get(learner=self.learner, is_active=True).pk, self.participant.pk)
            self.assertEqual(self.learner.enrolled, "0")

    def test_change_details(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('auth.change_details'))
        self.assertEqual(resp.status_code, 200)

        # no change
        resp = self.client.post(reverse("auth.change_details"), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No changes made.")

        # invalid old_number
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '012'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please enter a valid mobile number.")

        # incorrect old_number
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27721234567'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This number is not associated with this account.")

        # invalid new_mobile
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27123456789',
                                      'new_number': '012'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please enter a valid mobile number.")

        # invalid new_mobile
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27123456789',
                                      'new_number': '+27123456789'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "You cannot change your number to your current number.")

        # new number same as an existing user
        learner = self.create_learner(
            self.school,
            username="+271234569999",
            mobile="+27123456999",
            email="abcd@abcd.com")

        self.participant = self.create_participant(
            learner,
            self.classs,
            datejoined=datetime.now())

        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27123456789',
                                      'new_number': '+27123456999'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A user with this mobile number (+27123456999) already exists.")

        self.learner.email = "qwer@qwer.com"
        self.learner.save()
        # incorrect old_email
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_email': 'xyz@xyz.com'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This email is not associated with this account.")

        # changing to current email
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_email': 'qwer@qwer.com',
                                      'new_email': 'qwer@qwer.com'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This is your current email.")

        # invalid new_email
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_email': 'qwer@qwer.com',
                                      'new_email': 'abc'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please enter a valid email.")

        # email exists
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_email': 'qwer@qwer.com',
                                      'new_email': 'abcd@abcd.com'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A user with this email (abcd@abcd.com) already exists.")

        # valid
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27123456789',
                                      'new_number': '0721478529',
                                      'old_email': 'qwer@qwer.com',
                                      'new_email': 'asdf@asdf.com'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Your number has been changed to 0721478529")
        self.assertContains(resp, "Your email has been changed to asdf@asdf.com.")

    def test_participant_required_decorator(self):
        learner = self.create_learner(
            self.school,
            username="+27987654321",
            mobile="+27987654321",
            country="country",
            area="Test_Area",
            unique_token='cba321',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        participant = self.create_participant(
            learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.client.get(reverse('auth.autologin',
                                kwargs={'token': learner.unique_token}))

        # participant exists
        resp = self.client.get(reverse('learn.home'), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "WELCOME")

        # participant doesn't exist
        participant.delete()
        resp = self.client.get(reverse('learn.home'), follow=True)
        self.assertRedirects(resp, reverse('auth.login'))


class ProfanityTests(TestCase):
    fixtures = ['profanities.json']

    def test_profanities(self):
        contents = [
            "hellow boo",
            "What guys",
            "teboho...I have made the administrator aware of system failure....but also please lets us be careful on what we say....it should be all about maths and qwaqwa, tshiya maths from mr mdlalose",
            "no teboho",
            "Since I'm new in one plus but I have proved that this is the way to success in pro maths 2015.",
            "Since I'm new in one plus but I have proved that this is the way to success in pro maths.",
            "how is everyone doing with eucliean geometry grade 11?",
            "hmmm.....i think about it more than i forget ......i didnt practise the whole week last week and its something i am not proud of......but then i shall try my best ....",
            "Mine doesn't want to work. It keeps saying I should come tomorrow but tomorrow never comes. What should I do?",
            "What do I do if it doesn't want me to login everyday",
            "how did you deal with today's challenges",
            "How do u wim airtime ?",
            "hi im momelezi a maths student in kutlwanong",
            "yho your questions are tricky but they are good for us ''cause they open our minds",
            "thank u for revisions that u have given US",
            "revision and practise could not be any easy and effective as it is with oneplus. Guys do spread the world as better individuals we can make better friends, with better friends better school mates, with better school mates, with better school mates better schools, with better schools better communities, with better communities better countries, with better countries a better world. With a better world a better Future. Isn't that great?"
            ]
        for content in contents:
            self.assertEquals(contains_profanity(content), False, content)


class TestFlashMessage(TestCase):
    def create_learner(self, school, **kwargs):
        if 'grade' not in kwargs:
            kwargs['grade'] = 'Grade 11'
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        participant = Participant.objects.create(
            learner=learner, classs=classs, **kwargs)
        return participant

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

    def setUp(self):
        self.course = self.create_course()
        self.classs = self.create_class('Slytherin', self.course)
        self.organisation = self.create_organisation()
        self.school = self.create_school('Hogwarts', self.organisation)
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

    def test_discuss_flash_message(self):
        # User logs in to test commenting
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        self.test_question = self.create_test_question("question1", self.module, state=TestingQuestion.PUBLISHED)
        self.question_option_right = self.create_test_question_option("question1_right",
                                                                      self.test_question,
                                                                      correct=True)

        self.question_option_wrong = self.create_test_question_option("question1_wrong",
                                                                      self.test_question,
                                                                      correct=False)

        self.client.get(reverse("learn.next"))
        self.client.post(reverse("learn.next"), data={"answer": self.question_option_right.id}, follow=True)
        self.client.get(reverse("learn.right"))
        message = 'Sssssayiacchhhassiiiyyyeeth'
        empty_message = ''
        #Test 1.1: correct data given to show right.html
        resp = self.client.post(reverse('learn.right'),
                                data={'comment': message},
                                follow=True)
        self.assertContains(resp, "<p>%s</p>" % (message,), html=True)

        #Test 1.2: correct data given to show right.html with empty message
        resp = self.client.post(reverse('learn.right'),
                                data={'comment': empty_message},
                                follow=True)
        self.assertEquals(resp.status_code, 200)

        ParticipantQuestionAnswer.objects.all().delete()
        LearnerState.objects.all().delete()
        self.client.get(reverse("learn.next"))
        self.client.post(reverse("learn.next"), data={"answer": self.question_option_wrong.id}, follow=True)
        self.client.get(reverse("learn.wrong"))

        #Test 2.1: incorrect data given to show wrong.html
        message = 'He is just a puppy'
        resp = self.client.post(reverse('learn.wrong'),
                                data={'comment': message},
                                follow=True)
        self.assertContains(resp, message)

        #Test 2.2: incorrect data given to show wrong.html with empty message
        self.client.post(reverse('learn.wrong'),
                                data={'comment': empty_message},
                                follow=True)
        self.assertEquals(resp.status_code, 200)

        self.client.get(reverse("learn.redo"))
        self.client.post(reverse("learn.redo"), data={"answer": self.question_option_right.id}, follow=True)
        resp = self.client.get(reverse("learn.redo_right"))

        #Test 3.1: correct data given in redo to show redo_right.html
        message = 'My Father will hear about this'
        resp = self.client.post(reverse('learn.redo_right'),
                                data={'comment': message},
                                follow=True)
        self.assertContains(resp, "<p>%s</p>" % (message,), html=True)

        #Test 3.2: correct data given in redo to show redo_right.html with empty message
        resp = self.client.post(reverse('learn.redo_right'),
                                data={'comment': empty_message},
                                follow=True)
        self.assertEquals(resp.status_code, 200)

        ParticipantRedoQuestionAnswer.objects.all().delete()
        self.client.get(reverse("learn.redo"))
        self.client.post(reverse("learn.redo"), data={"answer": self.question_option_wrong.id}, follow=True)
        self.client.get(reverse("learn.redo_wrong"))

        #Test 4.1: incorrect data given in redo to show redo_wrong.html
        message = 'The boy who lived, come to die'
        resp = self.client.post(reverse('learn.redo_wrong'),
                                data={'comment': message},
                                follow=True)
        self.assertContains(resp, "<p>%s</p>" % (message,), html=True)

        #Test 4.2: incorrect data given in redo to show redo_wrong.html with empty message
        resp = self.client.post(reverse('learn.redo_wrong'),
                                data={'comment': empty_message},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
