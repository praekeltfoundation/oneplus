# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging

from django.core.urlresolvers import reverse
from django.test import TestCase
from core.models import Participant, Class, Course, ParticipantQuestionAnswer, ParticipantBadgeTemplateRel, Setting
from organisation.models import Organisation, School, Module, CourseModuleRel
from content.models import TestingQuestion, TestingQuestionOption, GoldenEgg, GoldenEggRewardLog, Event,\
    EventQuestionRel, EventSplashPage, EventStartPage, EventEndPage, EventQuestionAnswer, EventParticipantRel
from gamification.models import GamificationScenario, GamificationBadgeTemplate, GamificationPointBonus
from auth.models import Learner, CustomUser
from django.test.client import Client
from communication.models import Message, ChatGroup, ChatMessage, Post, Report, ReportResponse, Sms, SmsQueue, \
    Discussion, PostComment, Profanity
from .templatetags.oneplus_extras import format_content, format_option
from mock import patch
from .models import LearnerState
from .views import get_week_day
from oneplus.learn_views import get_badge_awarded, get_points_awarded
from oneplus.auth_views import space_available, validate_mobile
from .utils import get_today
from go_http.tests.test_send import RecordingHandler
from django.test.utils import override_settings
from django.db.models import Count
from oneplusmvp import settings
from django.conf import settings
from oneplus.tasks import update_perc_correct_answers_worker


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

    def create_event_start_page(self, event, header, paragraph):
        return EventStartPage.objects.create(event=event, header=header, paragraph=paragraph)

    def create_event_end_page(self, event, header, paragraph):
        return EventEndPage.objects.create(event=event, header=header, paragraph=paragraph)

    def create_event_splash_page(self, event, order_number, header, paragraph):
        return EventSplashPage.objects.create(event=event, order_number=order_number, header=header,
                                              paragraph=paragraph)

    def create_event_question(self, event, question, order):
        return EventQuestionRel.objects.create(event=event, question=question, order=order)

    def fake_mail_managers(subject, message, fail_silently):
        pass

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

    @patch("django.core.mail.mail_managers", fake_mail_managers)
    def test_home(self):
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
                                  datetime.now() + timedelta(days=1), number_sittings=2, event_points=5)
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
        self.assertContains(resp, end_page.header)

        resp = self.client.get(reverse('learn.home'))
        self.assertContains(resp, "5</span><br/>POINTS")

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

    def test_nextchallenge(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        #no questions
        resp = self.client.get(reverse('learn.next'), follow=True)
        self.assertRedirects(resp, "home", status_code=302, target_status_code=200)
        self.assertContains(resp, "ONEPLUS | WELCOME")

        #with question
        question1 = self.create_test_question(
            'question1', self.module, question_content='test question', state=3)

        TestingQuestionOption.objects.create(
            name='questionoption1',
            question=question1,
            content='questionanswer1',
            correct=True,
        )

        resp = self.client.get(reverse('learn.next'))
        self.assertEquals(resp.status_code, 200)

        self.assertContains(resp, 'test question')
        self.assertContains(resp, 'questionanswer1')

        resp = self.client.post(
            reverse('learn.next'),
            data={'page': 1},
            follow=True
        )
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('learn.next'),
            data={
                'answer': 99
            }, follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_event(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        #create event_session variable
        s = self.client.session
        s["event_session"] = True
        s.save()

        #no event
        resp = self.client.get(reverse('learn.event'))
        self.assertRedirects(resp, "home")

        #create event
        event = self.create_event("Test Event", self.course, activation_date=datetime.now() - timedelta(days=1),
                                  deactivation_date=datetime.now() + timedelta(days=1))
        start_page = self.create_event_start_page(event, "Test Start Page", "Test Paragraph")
        event_module = self.create_module("Event Module", self.course, type=2)

        #create event_session variable
        s = self.client.session
        s["event_session"] = True
        s.save()

        #no event questions
        resp = self.client.get(reverse('learn.event'))
        self.assertRedirects(resp, "home")

        #add question to event
        question = self.create_test_question("Event Question", event_module, state=3)
        correct_option = self.create_test_question_option("question_1_option_1", question)
        incorrect_option = self.create_test_question_option("question_1_option_2", question, correct=False)
        self.create_event_question(event, question, 1)

        #delete EventParticipantRel before calling event_start_page
        EventParticipantRel.objects.filter(event=event, participant=self.participant).delete()

        #create event_session variable
        s = self.client.session
        s["event_session"] = True
        s.save()

        resp = self.client.get(reverse('learn.event'))
        self.assertEquals(resp.status_code, 200)

        #no data in post
        resp = self.client.post(reverse('learn.event'), follow=True)
        self.assertEquals(resp.status_code, 200)

        #invalid option
        resp = self.client.post(reverse('learn.event'),
                                data={'answer': 99},
                                follow=True)
        self.assertEquals(resp.status_code, 200)

        #valid correct answer
        resp = self.client.post(reverse('learn.event'),
                                data={'answer': correct_option.id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "event_right")

        #test event right post
        resp = self.client.post(reverse("learn.event_right"))
        self.assertEquals(resp.status_code, 200)

        EventQuestionAnswer.objects.filter(participant=self.participant, event=event, question=question).delete()

        #valid incorrect answer
        resp = self.client.post(reverse('learn.event'),
                                data={'answer': incorrect_option.id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "event_wrong")

        #test event right post
        resp = self.client.post(reverse("learn.event_wrong"))
        self.assertEquals(resp.status_code, 200)

    def test_event_right(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        s = self.client.session
        s["event_session"] = True
        s.save()

        resp = self.client.get(reverse("learn.event_right"))
        self.assertRedirects(resp, "home")

    def test_event_wrong(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        s = self.client.session
        s["event_session"] = True
        s.save()

        resp = self.client.get(reverse("learn.event_wrong"))
        self.assertRedirects(resp, "home")

    def fake_update_all_perc_correct_answers():
        update_perc_correct_answers_worker('24hr', 1)
        update_perc_correct_answers_worker('48hr', 2)
        update_perc_correct_answers_worker('7days', 7)
        update_perc_correct_answers_worker('32days', 32)

    @patch('oneplus.learn_views.update_all_perc_correct_answers.delay', side_effect=fake_update_all_perc_correct_answers)
    def test_answer_correct_nextchallenge(self, mock_task):
        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': self.learner.unique_token})
        )

        # Create a question
        question1 = self.create_test_question(
            'question1', self.module, question_content='test question', state=3)
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

    @patch('oneplus.learn_views.update_all_perc_correct_answers.delay', side_effect=fake_update_all_perc_correct_answers)
    def test_answer_incorrect_nextchallenge(self, mock_task):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        # Create a question
        question1 = self.create_test_question(
            'question1', self.module, question_content='test question', state=3)
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
            data={'comment': 'test'}, follow=True
        )

        self.assertEquals(resp.status_code, 200)

        disc = Discussion.objects.all().first()

        resp = self.client.post(
            reverse('learn.right'),
            data={
                'reply': 'test',
                "reply_button": disc.id
            },
            follow=True
        )

        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Discussion.objects.all().count(), 2)

        resp = self.client.post(
            reverse('learn.right'),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

    def test_wronganswer(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )

        question1 = self.create_test_question(
            'question1',
            self.module,
            question_content='test question'
        )

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

        disc = Discussion.objects.all().first()

        resp = self.client.post(
            reverse('learn.wrong'),
            data={
                'reply': 'test',
                "reply_button": disc.id
            },
            follow=True
        )

        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Discussion.objects.all().count(), 2)

        resp = self.client.post(
            reverse('learn.wrong'),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

    def test_event_splash_page(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )

        #no event
        resp = self.client.get(reverse('learn.event_splash_page'))
        self.assertRedirects(resp, "home")

        #create event
        event = self.create_event("Test Event", self.course, activation_date=datetime.now() - timedelta(days=1),
                                  deactivation_date=datetime.now() + timedelta(days=1))
        splash_page = self.create_event_splash_page(event, 1, "Test Splash Page", "Test Paragraph")
        event_module = self.create_module("Event Module", self.course, type=2)
        question = self.create_test_question("Event Question", event_module, state=3)
        self.create_event_question(event, question, 1)

        resp = self.client.get(reverse('learn.event_splash_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, splash_page.header)

        resp = self.client.post(reverse('learn.event_splash_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, splash_page.header)

        EventParticipantRel.objects.create(event=event, participant=self.participant, sitting_number=1)

        resp = self.client.get(reverse('learn.event_splash_page'))
        self.assertRedirects(resp, "home")

    def test_event_start_page(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )

        #no event
        resp = self.client.get(reverse('learn.event_start_page'))
        self.assertRedirects(resp, "home")

        #create event
        event = self.create_event("Test Event", self.course, activation_date=datetime.now() - timedelta(days=1),
                                  deactivation_date=datetime.now() + timedelta(days=1))
        start_page = self.create_event_start_page(event, "Test Start Page", "Test Paragraph")
        event_module = self.create_module("Event Module", self.course, type=2)
        question = self.create_test_question("Event Question", event_module, state=3)
        self.create_event_question(event, question, 1)

        #with event
        resp = self.client.get(reverse('learn.event_start_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, start_page.header)

        #no data in post
        resp = self.client.post(reverse("learn.event_start_page"), data={}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, start_page.header)

        resp = self.client.post(reverse("learn.event_start_page"),
                                data={"event_start_button": "Get Started"}, follow=True)
        self.assertRedirects(resp, "event")
        self.assertContains(resp, "EVENT")

        #attempt to load start page again
        resp = self.client.get(reverse("learn.event_start_page"))
        self.assertRedirects(resp, "home")

        #change to multiple sittings
        event.number_sittings = 2
        event.save()

        resp = self.client.post(reverse("learn.event_start_page"),
                                data={"event_start_button": "Get Started"}, follow=True)
        self.assertRedirects(resp, "event")
        event_participant_rel = EventParticipantRel.objects.get(event=event, participant=self.participant)
        self.assertEquals(event_participant_rel.sitting_number, 2)

    def test_event_end_page(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )

        #create event_session variable
        s = self.client.session
        s["event_session"] = True
        s.save()

        resp = self.client.get(reverse('learn.event_end_page'))
        self.assertRedirects(resp, "home")

        spot_test = GamificationBadgeTemplate.objects.create(name="Spot Test 1")
        badge = GamificationScenario.objects.create(name="Spot Test 1", badge=spot_test, event="SPOT_TEST_1",
                                                    module=self.module, course=self.course)

        event = Event.objects.create(name="Spot Test event", course=self.course, activation_date=datetime.now(),
                                     deactivation_date=datetime.now() + timedelta(days=1), event_points=5, airtime=5,
                                     event_badge=badge)
        for i in range(1, 6):
            EventParticipantRel.objects.create(event=event, participant=self.participant, sitting_number=1)
        question = self.create_test_question("Event question", self.module)
        question_option = self.create_test_question_option("Option 1", question, True)
        EventQuestionRel.objects.create(event=event, question=question, order=1)
        EventQuestionAnswer.objects.create(event=event, participant=self.participant, question=question,
                                           question_option=question_option, correct=True, answer_date=datetime.now())
        EventEndPage.objects.create(event=event, header="Test End Page", paragraph="Test")

        resp = self.client.get(reverse('learn.event_end_page'))

        pbtr = ParticipantBadgeTemplateRel.objects.filter(badgetemplate=spot_test, scenario=badge,
                                                          participant=self.participant)

        _participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Test End Page")
        self.assertEquals(_participant.points, 5)
        self.assertIsNotNone(pbtr)

        event.name = "Exam"
        event.save()

        resp = self.client.get(reverse('learn.event_end_page'))

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Test End Page")

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
            course=self.course,
            publishdate=datetime.now()
        )
        blog.save()

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

    def test_smspassword_get(self):
        resp = self.client.get(reverse('auth.smspassword'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_smspassword_post(self):
        # invalid form
        resp = self.client.post(
            reverse('auth.smspassword'),
            {
                'msisdn': '+2712345678',

            },
            follow=True
        )

        self.assertEqual(resp.status_code, 200)

        # incorrect msisdn
        resp = self.client.post(
            reverse('auth.smspassword'),
            {
                'msisdn': '+2712345678',

            },
            follow=True
        )

        self.assertEqual(resp.status_code, 200)

        # correct msisdn
        resp = self.client.post(
            reverse('auth.smspassword'),
            {
                'msisdn': '+27123456789'

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
        answered = list(learnerstate.get_answers_this_week().order_by("question"))

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

        self.assertContains(resp, "Incorrect")

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

    @patch("django.core.mail.mail_managers", fake_mail_managers)
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
            }
        )
        self.assertContains(resp, "Your message has been sent. We will get back to you in the next 24 hours")

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

        self.assertContains(resp, "SIGN IN")

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

        self.assertContains(resp, "OnePlus is currently in test phase")

        learner = Learner.objects.create_user(
            username="+27231231231",
            mobile="+27231231231",
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

        for x in range(0, 11):
            question = self.create_test_question('question_%s' % x,
                                                 self.module,
                                                 question_content='test question',
                                                 state=3)
            question_option = self.create_test_question_option('question_option_%s' % x, question)

            question_list.append(question)
            question_option_list.append(question_option)

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

            if counter < 5:
                for y in range(0, counter+1):
                    all_particpants[counter].answer(question_list[y], question_option_list[y])


            #data for class leaderboard
            new_class = self.create_class('class_%s' % x, self.course)
            all_learners_classes.append(self.create_learner(self.school,
                                                            first_name="test_%s" % x,
                                                            username="08612345%s" % x,
                                                            mobile="08612345%s" % x,
                                                            unique_token='abc%s' % x,
                                                            unique_token_expiry=datetime.now() + timedelta(days=30)))
            all_learners_classes[counter].set_password(password)

            all_particpants_classes.append(self.create_participant(all_learners_classes[counter],
                                                                   new_class, datejoined=datetime.now()))

            counter += 1

        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': "20"})
        )
        resp = self.client.get(reverse('prog.leader'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.leader'), follow=True)
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.leader'), data={'overall': 'Overall Leaderboard'}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_20")
        self.assertContains(resp, "11th place")
        self.assertContains(resp, "2 Week Leaderboard")
        self.assertContains(resp, "3 Month Leaderboard")
        self.assertContains(resp, "Class Leaderboard")

        resp = self.client.post(reverse('prog.leader'), data={'two_week': '2 Week Leaderboard'}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_20")
        self.assertContains(resp, "11th place")
        self.assertContains(resp, "Overall Leaderboard")
        self.assertContains(resp, "3 Month Leaderboard")
        self.assertContains(resp, "Class Leaderboard")

        resp = self.client.post(reverse('prog.leader'), data={'three_month': '3 Month Leaderboard'}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_20")
        self.assertContains(resp, "11th place")
        self.assertContains(resp, "Overall Leaderboard")
        self.assertContains(resp, "2 Week Leaderboard")
        self.assertContains(resp, "Class Leaderboard")

        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': "14"})
        )

        resp = self.client.post(reverse('prog.leader'), data={'overall': 'Overall Leaderboard'}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_14")
        self.assertContains(resp, "1st place")
        self.assertContains(resp, "2 Week Leaderboard")
        self.assertContains(resp, "3 Month Leaderboard")
        self.assertContains(resp, "Class Leaderboard")

        resp = self.client.post(reverse('prog.leader'), data={'two_week': '2 Week Leaderboard'}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_14")
        self.assertContains(resp, "1st place")
        self.assertContains(resp, "Overall Leaderboard")
        self.assertContains(resp, "3 Month Leaderboard")
        self.assertContains(resp, "Class Leaderboard")

        resp = self.client.post(reverse('prog.leader'), data={'three_month': '3 Month Leaderboard'}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_14")
        self.assertContains(resp, "1st place")
        self.assertContains(resp, "Overall Leaderboard")
        self.assertContains(resp, "2 Week Leaderboard")
        self.assertContains(resp, "Class Leaderboard")

        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': "abc20"})
        )

        resp = self.client.post(reverse('prog.leader'), data={'class': 'Class Leaderboard'}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "class_20")
        self.assertContains(resp, "13th place")
        self.assertContains(resp, "Overall Leaderboard")
        self.assertContains(resp, "2 Week Leaderboard")
        self.assertContains(resp, "3 Month Leaderboard")

        all_particpants_classes[counter-1].answer(question, question_option)

        resp = self.client.post(reverse('prog.leader'), data={'class': 'Class Leaderboard'}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "class_20")
        self.assertContains(resp, "2nd place")
        self.assertContains(resp, "Overall Leaderboard")
        self.assertContains(resp, "2 Week Leaderboard")
        self.assertContains(resp, "3 Month Leaderboard")

        resp = self.client.post(reverse('prog.leader'), data={'leader_menu': 'leader_menu'}, follow=True)
        self.assertEquals(resp.status_code, 200)
        resp = self.client.post(reverse('prog.leader'), data={'region': 'region'}, follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_ontrack_screen(self):
        self.client.get(
            reverse('auth.autologin',
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

        resp = self.client.post(
            reverse('com.bloglist'),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

    def test_smspassword_get2(self):
        resp = self.client.get(reverse('auth.smspassword'), follow=True)
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
        # csv no region
        resp = c.get(reverse('reports.learner', kwargs={'mode': 1, 'region': ''}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv'))

        # xls no region
        resp = c.get(reverse('reports.learner', kwargs={'mode': 2, 'region': ''}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('xls'))

        # csv + region
        resp = c.get(reverse('reports.learner', kwargs={'mode': 1, 'region': 'Test_Area'}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv', 'Test_Area'))
        self.assertContains(resp, 'MSISDN,First Name,Last Name,School,Region,Questions Completed,Percentage Correct')
        self.assertContains(resp, '+27123456789,,,school name,Test_Area,1,100')

        # csv + region that doesn't exist
        resp = c.get(reverse('reports.learner', kwargs={'mode': 1, 'region': 'Test_Area44'}))
        self.assertEquals(resp.get('Content-Disposition'), make_content('csv', 'Test_Area44'))
        self.assertContains(resp, 'MSISDN,First Name,Last Name,School,Region,Questions Completed,Percentage Correct')
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

    def test_get_users(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        resp = c.get('/users/all')
        self.assertContains(resp, '"name": "+27123456789"')

        resp = c.get('/users/%s' % self.classs.id)
        self.assertContains(resp, '"name": "+27123456789"')

        resp = c.get('/users/abc')
        self.assertEquals(resp.status_code, 200)

        resp = c.get('/users/%s' % 99)
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
        self.assertContains(resp, "<title>ONEPLUS | HELLO</title>")

    def test_validate_mobile(self):
        v_mobile_1 = "0721234567"
        v_mobile_1 = validate_mobile(v_mobile_1)
        self.assertEquals(v_mobile_1, "0721234567")

        v_mobile_2 = "+27721234569"
        v_mobile_2 = validate_mobile(v_mobile_2)
        self.assertEquals(v_mobile_2, "+27721234569")

        v_mobile_3 = "+123721234567"
        v_mobile_3 = validate_mobile(v_mobile_3)
        self.assertEquals(v_mobile_3, "+123721234567")

        i_mobile_1 = "072123456"
        i_mobile_1 = validate_mobile(i_mobile_1)
        self.assertEquals(i_mobile_1, None)

        i_mobile_2 = "07212345678"
        i_mobile_2 = validate_mobile(i_mobile_2)
        self.assertEquals(i_mobile_2, None)

        i_mobile_3 = "+2821234567"
        i_mobile_3 = validate_mobile(i_mobile_3)
        self.assertEquals(i_mobile_3, None)

        i_mobile_4 = "+1237212345678"
        i_mobile_4 = validate_mobile(i_mobile_4)
        self.assertEquals(i_mobile_4, None)

    @patch("django.core.mail.mail_managers", fake_mail_managers)
    def test_signup_form(self):
        province_school = School.objects.get(name="Open School")
        resp = self.client.get(reverse('auth.signup_form'))
        self.assertEqual(resp.status_code, 200)

        # no data given
        resp = self.client.post(reverse('auth.signup_form'),
                                data={},
                                follow=True)
        self.assertContains(resp, "This must be completed", count=6)

        # invalid cellphone, grade and province
        resp = self.client.post(reverse('auth.signup_form'),
                                data={
                                    'first_name': self.learner.first_name,
                                    'surname': self.learner.last_name,
                                    'cellphone': '12345',
                                    'grade': 'Grade 12',
                                    'province': 'Wrong province name',
                                    'enrolled': 0,
                                },
                                follow=True)
        self.assertContains(resp, "Enter a valid cellphone number")
        self.assertContains(resp, "Select your grade")
        self.assertContains(resp, "Select your province")

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
        resp = self.client.get(reverse('auth.signup_form_promath'), follow=True)
        self.assertContains(resp, "Sign Up")

        #no data
        resp = self.client.post(reverse('auth.signup_form_promath'), follow=True)
        self.assertContains(resp, "Sign Up")

        #no school and class
        resp = self.client.post(reverse('auth.signup_form_promath'),
                                data={
                                    'first_name': "Bob",
                                    'surname': "Bobby",
                                    'cellphone': '0729876543',
                                    'province': 'Gauteng',
                                    'grade': 'Grade 10',
                                    'enrolled': 0,
                                },
                                follow=True)
        self.assertContains(resp, "This must be completed", count=2)

        #invalid school and class
        resp = self.client.post(reverse('auth.signup_form_promath'),
                                data={
                                    'first_name': "Bob",
                                    'surname': "Bobby",
                                    'cellphone': '0729876543',
                                    'province': 'Gauteng',
                                    'grade': 'Grade 10',
                                    'enrolled': 0,
                                    'school': 999,
                                    'classs': 999
                                },
                                follow=True)
        self.assertContains(resp, "Select your school")
        self.assertContains(resp, "Select your class")

        #valid data
        resp = self.client.post(reverse('auth.signup_form_promath'),
                                data={
                                    'first_name': "Bob",
                                    'surname': "Bobby",
                                    'cellphone': '0729876543',
                                    'province': 'Gauteng',
                                    'grade': 'Grade 10',
                                    'enrolled': 0,
                                    'school': self.school.id,
                                    'classs': self.classs.id
                                },
                                follow=True)
        self.assertContains(resp, "Thank you")
        new_learner = Learner.objects.get(username='0729876543')
        self.assertEquals('Bob', new_learner.first_name)

        # valid - not enrolled - grade 10 - no open class created
        resp = self.client.post(reverse('auth.signup_form'),
                                data={
                                    'first_name': "Koos",
                                    'surname': "Botha",
                                    'cellphone': '0729876540',
                                    'grade': 'Grade 10',
                                    'province': "Gauteng",
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
        resp = self.client.post(reverse('auth.signup_form'),
                                data={
                                    'first_name': "Willy",
                                    'surname': "Wolly",
                                    'cellphone': '0729878963',
                                    'grade': 'Grade 10',
                                    'province': "Gauteng",
                                    'enrolled': 1,
                                },
                                follow=True)
        self.assertContains(resp, "Thank you")
        new_learner = Learner.objects.get(username='0729878963')
        self.assertEquals('Willy', new_learner.first_name)

        # valid - not enrolled - grade 11 - creaing open class
        resp = self.client.post(reverse('auth.signup_form'),
                                data={
                                    'first_name': "Tom",
                                    'surname': "Tom",
                                    'cellphone': '0729876576',
                                    'grade': 'Grade 11',
                                    'province': "Gauteng",
                                    'enrolled': 1,
                                },
                                follow=True)
        self.assertContains(resp, "Thank you")
        new_learner = Learner.objects.get(username='0729876576')
        self.assertEquals('Tom', new_learner.first_name)

        # valid - not enrolled - grade 11
        resp = self.client.post(reverse('auth.signup_form'),
                                data={
                                    'first_name': "Henky",
                                    'surname': "Tanky",
                                    'cellphone': '0729876486',
                                    'grade': 'Grade 11',
                                    'province': "Gauteng",
                                    'enrolled': 1,
                                },
                                follow=True)
        self.assertContains(resp, "Thank you")
        new_learner = Learner.objects.get(username='0729876486')
        self.assertEquals('Henky', new_learner.first_name)

        resp = self.client.get(reverse("auth.signup_form_promath"))
        self.assertContains(resp, 'To sign up please complete the following information:')

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

    def test_golden_egg(self):
        new_learner = self.create_learner(
            self.school,
            username="+27761234567",
            mobile="+27761234567",
            unique_token='123456789',
            unique_token_expiry=datetime.now() + timedelta(days=30))

        new_participant = self.create_participant(new_learner, self.classs, datejoined=datetime.now())

        q = self.create_test_question('question_1', module=self.module, state=3)
        q_o = self.create_test_question_option('question_option_1', q)

        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': new_learner.unique_token})
        )

        #GOLDEN EGG DOESN'T EXIST
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

        #GOLDEN EGG INACTIVE
        golden_egg = GoldenEgg.objects.create(course=self.course, classs=self.classs, active=False, point_value=5)

        #set the golden egg number to 1
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

        #GOLDEN EGG ACTIVE - TEST POINTS
        golden_egg.active = True
        golden_egg.save()

        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=new_participant).first()
        state.golden_egg_question = 1
        state.save()
        self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)
        new_participant = Participant.objects.filter(learner=new_learner).first()

        self.assertEquals(6, new_participant.points)
        log = GoldenEggRewardLog.objects.filter(participant=new_participant, points=5).count()
        self.assertEquals(1, log)

        ParticipantQuestionAnswer.objects.filter(participant=new_participant,
                                                 question=q,
                                                 option_selected=q_o).delete()

        #TEST AIRTIME
        golden_egg.point_value = None
        golden_egg.airtime = 5
        golden_egg.save()

        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=new_participant).first()
        state.golden_egg_question = 1
        state.save()
        self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)

        log = GoldenEggRewardLog.objects.filter(participant=new_participant, airtime=5).count()
        self.assertEquals(1, log)

        ParticipantQuestionAnswer.objects.filter(participant=new_participant,
                                                 question=q,
                                                 option_selected=q_o).delete()
        new_participant.points = 0
        new_participant.save()

        #TEST BADGE
        bt1 = GamificationBadgeTemplate.objects.get(name="Golden Egg")
        sc1 = GamificationScenario.objects.get(name="Golden Egg")

        golden_egg.airtime = None
        golden_egg.badge = sc1
        golden_egg.save()

        self.client.get(reverse('learn.next'))
        state = LearnerState.objects.filter(participant=new_participant).first()
        state.golden_egg_question = 1
        state.save()
        self.client.post(reverse('learn.next'), data={'answer': q_o.id}, follow=True)
        new_participant = Participant.objects.filter(learner=new_learner).first()

        cnt = ParticipantBadgeTemplateRel.objects.filter(
            participant=new_participant,
            badgetemplate=bt1,
            scenario=sc1
        ).count()
        self.assertEquals(cnt, 1)
        # we are using the existing golden egg basge with no points
        self.assertEquals(1, new_participant.points)
        log = GoldenEggRewardLog.objects.filter(participant=new_participant, badge=sc1).count()
        self.assertEquals(1, log)
        #check log


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

        # Begin: Monday the 18th of August
        self.assertEquals(week_range[0], datetime(2014, 8, 18, 0, 0))

        # End: Friday the 22nd of August
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


class MessageTest(TestCase):
    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_school(self, name, organisation, **kwargs):
        return School.objects.create(name=name, organisation=organisation, **kwargs)

    def create_course(self, name="course1", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_admin(self, username, password, mobile):
        return CustomUser.objects.create_superuser(
            username=username,
            email='asdf@example.com',
            password=password,
            mobile=mobile)

    def create_learner(self, school, **kwargs):
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        return Participant.objects.create(learner=learner, classs=classs, **kwargs)

    def setUp(self):
        self.organisation = self.create_organisation()
        self.school = self.create_school("abc", self.organisation)
        self.course = self.create_course()
        self.classs = self.create_class("class1", self.course)

    def test_add_message(self):
        password = "12345"
        admin = self.create_admin("asdf", password, "+27123456789")
        c = Client()
        c.login(username=admin.username, password=password)

        # create a participant in course 1 class 1
        leaner_1 = self.create_learner(self.school, mobile="+27987654321", country="country", username="+27987654321")
        self.create_participant(leaner_1, self.classs, datejoined=datetime.now())

        # create another class in same course
        c1_class2 = self.create_class("c1_class2", self.course)

        # create a participant in course 1 class 2
        leaner_2 = self.create_learner(self.school, mobile="+27147852369", country="country", username="+27147852369")
        self.create_participant(leaner_2, c1_class2, datejoined=datetime.now())

        # create a new course and a class
        course2 = self.create_course("course2")
        c2_class1 = self.create_class("c2_class1", course2)

        # create a participant in course 2 class 1
        leaner_3 = self.create_learner(self.school, mobile="+27963258741", country="country", username="+27963258741")
        self.create_participant(leaner_3, c2_class1, datejoined=datetime.now())

        # create another class in course 2
        c2_class2 = self.create_class("c2_class2", course2)

        # create a participant in course 1 class 2
        leaner_4 = self.create_learner(self.school, mobile="+27123654789", country="country", username="+27123654789")
        self.create_participant(leaner_4, c2_class2, datejoined=datetime.now())

        # test date and content validation errors
        resp = c.post(reverse('com.add_message'),
                      data={'name': '',
                            'course': 'all',
                            'to_class': 'all',
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': '',
                            'publishdate_1': '',
                            'content': ''},
                      follow=True)
        self.assertContains(resp, 'This field is required')

        # test invalid date
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': 'all',
                            'to_class': 'all',
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': 'abc',
                            'publishdate_1': 'abc',
                            'content': 'message'},
                      follow=True)
        self.assertContains(resp, 'Please enter a valid date and time.')

        # test users list, all + user
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': 'all',
                            'users': ["all", "1"],
                            'direction': '1',
                            'publishdate_0': '2014-02-01',
                            'publishdate_1': '01:00:00',
                            'content': 'message'},
                      follow=True)
        self.assertContains(resp, 'Please make a valid learner selection')

        # test no data posted
        resp = c.post(reverse('com.add_message'), follow=True)
        self.assertContains(resp, 'This field is required')

        self.assertEquals(resp.status_code, 200)

        # send message to all course (4 messages, total 4)
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': 'all',
                            'to_class': 'all',
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': '2014-01-01',
                            'publishdate_1': '00:00:00',
                            'content': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 4)

        # send message to course 1 (2 messages, total 6)
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': 'all',
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': '2014-02-01',
                            'publishdate_1': '01:00:00',
                            'content': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 6)

        # send message to course 1 class 1 (1 messages, total 7)
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': '2014-03-01',
                            'publishdate_1': '02:00:00',
                            'content': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 7)

        # send message to course 1 class 1  learner 1(1 messages, total 8)
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': leaner_1.id,
                            'direction': '1',
                            'publishdate_0': '2014-04-03',
                            'publishdate_1': '03:00:00',
                            'content': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 8)

        # send message to course 1 class 1  learner 1(1 messages, total 9)
        # testing _save button
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': leaner_1.id,
                            'direction': '1',
                            'publishdate_0': '2014-04-03',
                            'publishdate_1': '03:00:00',
                            'content': 'message',
                            '_save': "_save"},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 9)
        self.assertContains(resp, "<title>Select Message to change | OnePlus site admin</title>")

        resp = c.get(reverse('com.add_message'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>Message</title>")

    def test_view_message(self):
        password = "12345"
        admin = self.create_admin("asdf", password, "+27123456789")
        c = Client()
        c.login(username=admin.username, password=password)

        leaner_1 = self.create_learner(self.school, mobile="+27987654321", country="country", username="+27987654321")
        self.create_participant(leaner_1, self.classs, datejoined=datetime.now())

        c.post(reverse('com.add_message'),
               data={'name': 'asdf',
                     'course': self.course.id,
                     'to_class': self.classs.id,
                     'users': leaner_1.id,
                     'direction': '1',
                     'publishdate_0': '2013-02-01',
                     'publishdate_1': '00:00:00',
                     'content': 'message'},
               follow=True)

        db_msg = Message.objects.all().first()

        resp = c.get(reverse('com.view_message', kwargs={'msg': 99}))

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Message not found")

        resp = c.get(reverse('com.view_message', kwargs={'msg': db_msg.id}))

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>Message</title>")

        resp = c.post(reverse('com.view_message', kwargs={'msg': db_msg.id}), follow=True)

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>Message</title>")


class SMSQueueTest(TestCase):
    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_school(self, name, organisation, **kwargs):
        return School.objects.create(name=name, organisation=organisation, **kwargs)

    def create_course(self, name="course1", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_admin(self, username, password, mobile):
        return CustomUser.objects.create_superuser(
            username=username,
            email='asdf@example.com',
            password=password,
            mobile=mobile)

    def create_learner(self, school, **kwargs):
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        return Participant.objects.create(learner=learner, classs=classs, **kwargs)

    def setUp(self):
        self.organisation = self.create_organisation()
        self.school = self.create_school("abc", self.organisation)
        self.course = self.create_course()
        self.classs = self.create_class("class1", self.course)

    def test_add_sms(self):
        password = "12345"
        admin = self.create_admin("asdf", password, "+27123456789")
        c = Client()
        c.login(username=admin.username, password=password)

        # create a participant in course 1 class 1
        learner_1 = self.create_learner(self.school, mobile="+27987654321", country="country", username="+27987654321")
        self.create_participant(learner_1, self.classs, datejoined=datetime.now())

        # create another class in same course
        c1_class2 = self.create_class("c1_class2", self.course)

        # create a participant in course 1 class 2
        learner_2 = self.create_learner(self.school, mobile="+27147852369", country="country", username="+27147852369")
        self.create_participant(learner_2, c1_class2, datejoined=datetime.now())

        # create a new course and a class
        course2 = self.create_course("course2")
        c2_class1 = self.create_class("c2_class1", course2)

        # create a participant in course 2 class 1
        learner_3 = self.create_learner(self.school, mobile="+27963258741", country="country", username="+27963258741")
        self.create_participant(learner_3, c2_class1, datejoined=datetime.now())

        # create another class in course 2
        c2_class2 = self.create_class("c2_class2", course2)

        # create a participant in course 1 class 2
        learner_4 = self.create_learner(self.school, mobile="+27123654789", country="country", username="+27123654789")
        self.create_participant(learner_4, c2_class2, datejoined=datetime.now())

        # send sms to all course (4 sms, total 4)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': 'all',
                            'to_class': 'all',
                            'users': 'all',
                            'date_sent_0': '2014-05-01',
                            'date_sent_1': '00:00:00',
                            'message': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 4)

        # send sms to course 1 (2 sms, total 6)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': 'all',
                            'users': 'all',
                            'date_sent_0': '2014-06-01',
                            'date_sent_1': '01:00:00',
                            'message': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 6)

        # send sms to course 1 class 1 (1 sms, total 7)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': 'all',
                            'date_sent_0': '2014-07-01',
                            'date_sent_1': '02:00:00',
                            'message': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 7)

        # send sms to course 1 class 1 (1 sms, total 8)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': learner_1.id,
                            'date_sent_0': '2014-07-01',
                            'date_sent_1': '02:00:00',
                            'message': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 8)

        # send sms to course 1 class 1 (1 sms, total 9)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': learner_1.id,
                            'date_sent_0': '2014-07-01',
                            'date_sent_1': '02:00:00',
                            'message': 'message',
                            '_save': '_save'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 9)
        self.assertContains(resp, "<title>Select Queued Sms to change | OnePlus site admin</title>")

        resp = c.get(reverse('com.add_sms'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>SMS</title>")

        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'date_sent_0': '',
                            'date_sent_1': '',
                            'message': ''},
                      follow=True)
        self.assertContains(resp, 'This field is required')

        # testing _save button
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'date_sent_0': '1900-01-01',
                            'date_sent_1': 'abc',
                            'message': ''},
                      follow=True)
        self.assertContains(resp, 'This field is required')

        resp = c.post(reverse('com.add_sms'), follow=True)
        self.assertContains(resp, 'This field is required')

    def test_view_sms(self):
        password = "12345"
        admin = self.create_admin("asdf", password, "+27123456789")
        c = Client()
        c.login(username=admin.username, password=password)

        learner_1 = self.create_learner(self.school, mobile="+27987654321", country="country", username="+27987654321")
        self.create_participant(learner_1, self.classs, datejoined=datetime.now())

        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': self.classs.id,
                            'users': learner_1.id,
                            'date_sent_0': datetime.now().time(),
                            'date_sent_1': datetime.now().date(),
                            'message': 'message'},
                      follow=True)

        db_sms = SmsQueue.objects.all().first()

        resp = c.get(reverse('com.view_sms', kwargs={'sms': 99}))

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Queued SMS not found")

        resp = c.get(reverse('com.view_sms', kwargs={'sms': db_sms.id}))

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>SMS</title>")

        resp = c.post(reverse('com.view_sms', kwargs={'sms': db_sms.id}), follow=True)

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>SMS</title>")


class ExtraAdminBitTests(TestCase):
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

    def create_post(self, name="Test Post", description="Test", content="Test content"):
        return Post.objects.create(
            name=name,
            description=description,
            course=self.course,
            content=content,
            publishdate=datetime.now(),
            moderated=True
        )

    def create_post_comment(self, post, author, content="Test Content"):
        return PostComment.objects.create(
            author=author,
            post=post,
            content=content,
            publishdate=datetime.now()
        )

    def create_chat_group(self, course, name="Test Chat Group", description="Test"):
        return ChatGroup.objects.create(
            name=name,
            description=description,
            course=course
        )

    def create_chat_message(self, chat_group, author, content="Test"):
        return ChatMessage.objects.create(
            chatgroup=chat_group,
            author=author,
            content=content,
            publishdate=datetime.now()
        )

    def create_and_answer_questions(self, num_questions, prefix, date, correct=False):
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
                answerdate=date,
                correct=correct
            )
            answer.save()
            answers.append(answer)

        return answers

    def create_test_question_option(self, name, question, correct=True):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=correct)

    def create_test_answer(
            self,
            participant,
            question,
            option_selected,
            answerdate,
            correct):
        return ParticipantQuestionAnswer.objects.create(
            participant=participant,
            question=question,
            option_selected=option_selected,
            answerdate=answerdate,
            correct=correct
        )

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

        self.chat_group = self.create_chat_group(self.course)

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
                      data={
                          'title': '',
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/report_response/%s' % rep.id,
                      data={
                          'title': '',
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
                      data={
                          'title': 'test',
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        self.assertEquals(ReportResponse.objects.all().count(), rr_cnt + 1)
        self.assertEquals(Message.objects.all().count(), msg_cnt + 1)

        resp = c.get('/report_response/%s' % rep.id)
        self.assertContains(resp, 'Report Response')

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
                      data={
                          'title': '',
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/message_response/%s' % msg.id,
                      data={
                          'title': '',
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('/message_response/%s' % msg.id)
        self.assertContains(resp, 'This field is required.')

        msg_cnt = Message.objects.all().count()

        resp = c.post('/message_response/%s' % msg.id,
                      data={
                          'title': 'test',
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
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/sms_response/%s' % sms.id,
                      data={
                          'title': '',
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('/sms_response/%s' % sms.id)
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/sms_response/%s' % sms.id,
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': 'Test24'
                      })

        sms = Sms.objects.get(pk=sms.id)
        self.assertEquals(sms.responded, True)
        self.assertEquals(sms.respond_date.date(), datetime.now().date())
        self.assertIsNotNone(sms.response)

        qsms = SmsQueue.objects.get(msisdn=learner.mobile)
        self.assertEquals(qsms.message, 'Test24')

        resp = c.get('/sms_response/%s' % sms.id)
        self.assertContains(resp, 'Respond to SMS')

    def test_admin_discussion_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        burl = '/discussion_response/'

        question = self.create_test_question('q7', self.module)

        resp = c.get('%s1000' % burl)
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

        resp = c.get('%s%s' % (burl, disc.id))
        self.assertContains(resp, 'Participant not found')

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 3, 18, 1, 1)
        )

        resp = c.get('%s%s' % (burl, disc.id))
        self.assertContains(resp, 'Respond to Discussion')

        resp = c.post('%s%s' % (burl, disc.id),
                      data={
                          'title': '',
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, disc.id),
                      data={
                          'title': '',
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s' % (burl, disc.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, disc.id),
                      data={
                          'title': 'test',
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        disc = Discussion.objects.get(pk=disc.id)
        self.assertIsNotNone(disc.response)
        self.assertEquals(disc.response.moderated, True)
        self.assertEquals(disc.response.author, self.admin_user)

        resp = c.get('%s%s' % (burl, disc.id))
        self.assertContains(resp, 'Respond to Discussion')

    def test_admin_discussion_response_selected(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        burl = '/discussion_response_selected/'

        question = self.create_test_question('q9', self.module)

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'All the selected Discussions have been responded too')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456888",
            mobile="+27223456888",
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

        disc2 = Discussion.objects.create(
            name='Test',
            description='Test',
            content='Test content again',
            author=learner,
            publishdate=datetime.now(),
            course=self.course,
            module=self.module,
            question=question
        )

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 3, 18, 1, 1)
        )

        resp = c.get('%s%s,%s' % (burl, disc.id, disc2.id))
        self.assertContains(resp, 'Respond to Selected')

        resp = c.post('%s%s,%s' % (burl, disc.id, disc2.id),
                      data={
                          'title': '',
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, disc.id, disc2.id),
                      data={
                          'title': '',
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s,%s' % (burl, disc.id, disc2.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, disc.id, disc2.id),
                      data={
                          'title': 'test',
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        disc = Discussion.objects.get(pk=disc.id)
        disc2 = Discussion.objects.get(pk=disc2.id)
        self.assertIsNotNone(disc.response)
        self.assertEquals(disc.response.moderated, True)
        self.assertEquals(disc.response.author, self.admin_user)
        self.assertIsNotNone(disc2.response)
        self.assertEquals(disc2.response.moderated, True)
        self.assertEquals(disc2.response.author, self.admin_user)

    def test_admin_blog_comment_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        burl = '/blog_comment_response/'

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'PostComment 1000 not found')

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

        post = self.create_post()
        c1 = self.create_post_comment(post, learner)

        resp = c.get('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'Respond to Blog Comment')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        pc = PostComment.objects.get(pk=c1.id)
        self.assertIsNotNone(pc.response)
        self.assertEquals(pc.response.moderated, True)
        self.assertEquals(pc.response.author, self.admin_user)

        resp = c.get('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'Respond to Blog Comment')

    def test_admin_blog_comment_response_selected(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        burl = '/blog_comment_response_selected/'

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'All the selected Blog Comments have been responded too')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456888",
            mobile="+27223456888",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        post = self.create_post()
        pc1 = self.create_post_comment(post, learner)
        pc2 = self.create_post_comment(post, learner)

        resp = c.get('%s%s,%s' % (burl, pc1.id, pc2.id))
        self.assertContains(resp, 'Respond to Selected')

        resp = c.post('%s%s,%s' % (burl, pc1.id, pc2.id),
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, pc1.id, pc2.id),
                      data={
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s,%s' % (burl, pc1.id, pc2.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, pc1.id, pc2.id),
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        pc1 = PostComment.objects.get(pk=pc1.id)
        pc2 = PostComment.objects.get(pk=pc2.id)
        self.assertIsNotNone(pc1.response)
        self.assertEquals(pc1.response.moderated, True)
        self.assertEquals(pc1.response.author, self.admin_user)
        self.assertIsNotNone(pc2.response)
        self.assertEquals(pc2.response.moderated, True)
        self.assertEquals(pc2.response.author, self.admin_user)
        # because we are posting to the same blog only one reply is made
        self.assertEquals(pc1.response.id, pc2.response.id)

    def test_admin_chat_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        burl = '/chat_response/'

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'ChatMessage 1000 not found')

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

        c1 = self.create_chat_message(self.chat_group, learner)

        resp = c.get('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'Respond to Chat Message')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        cm = ChatMessage.objects.get(pk=c1.id)
        self.assertIsNotNone(cm.response)
        self.assertEquals(cm.response.moderated, True)
        self.assertEquals(cm.response.author, self.admin_user)

        resp = c.get('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'Respond to Chat Message')

    def test_admin_chat_response_selected(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        burl = '/chat_response_selected/'

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'All the selected Chat Messages have been responded too')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456888",
            mobile="+27223456888",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        c1 = self.create_chat_message(self.chat_group, learner)
        c2 = self.create_chat_message(self.chat_group, learner)

        resp = c.get('%s%s,%s' % (burl, c1.id, c2.id))
        self.assertContains(resp, 'Respond to Selected')

        resp = c.post('%s%s,%s' % (burl, c1.id, c2.id),
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, c1.id, c2.id),
                      data={
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s,%s' % (burl, c1.id, c2.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, c1.id, c2.id),
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        c1 = ChatMessage.objects.get(pk=c1.id)
        c2 = ChatMessage.objects.get(pk=c2.id)
        self.assertIsNotNone(c1.response)
        self.assertEquals(c1.response.moderated, True)
        self.assertEquals(c1.response.author, self.admin_user)
        self.assertIsNotNone(c2.response)
        self.assertEquals(c2.response.moderated, True)
        self.assertEquals(c2.response.author, self.admin_user)
        # because we are posting to the same chat group only one reply is made
        self.assertEquals(c1.response.id, c2.response.id)

    def admin_page_test_helper(self, c, page):
        resp = c.get(page)
        self.assertEquals(resp.status_code, 200)

    def test_auth_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/")

        self.admin_page_test_helper(c, "/admin/auth/")
        self.admin_page_test_helper(c, "/admin/auth/coursemanager/")
        self.admin_page_test_helper(c, "/admin/auth/coursementor/")
        self.admin_page_test_helper(c, "/admin/auth/group/")
        self.admin_page_test_helper(c, "/admin/auth/learner/")
        self.admin_page_test_helper(c, "/admin/auth/learner/?tf=1")
        self.admin_page_test_helper(c, "/admin/auth/teacher/")
        self.admin_page_test_helper(c, "/admin/auth/schoolmanager/")
        self.admin_page_test_helper(c, "/admin/auth/systemadministrator/")

    def test_communication_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/communication/")
        self.admin_page_test_helper(c, "/admin/communication/ban/")
        self.admin_page_test_helper(c, "/admin/communication/chatgroup/")
        self.admin_page_test_helper(c, "/admin/communication/chatmessage/")
        self.admin_page_test_helper(c, "/admin/communication/discussion/")
        self.admin_page_test_helper(c, "/admin/communication/message/")
        self.admin_page_test_helper(c, "/admin/communication/moderation/")
        self.admin_page_test_helper(c, "/admin/communication/postcomment/")
        self.admin_page_test_helper(c, "/admin/communication/post/")
        self.admin_page_test_helper(c, "/admin/communication/profanity/")
        self.admin_page_test_helper(c, "/admin/communication/smsqueue/")
        self.admin_page_test_helper(c, "/admin/communication/reportresponse/")
        self.admin_page_test_helper(c, "/admin/communication/report/")
        self.admin_page_test_helper(c, "/admin/communication/sms/")

    def test_content_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/content/")
        self.admin_page_test_helper(c, "/admin/content/learningchapter/")
        self.admin_page_test_helper(c, "/admin/content/mathml/")
        self.admin_page_test_helper(c, "/admin/content/testingquestionoption/")
        self.admin_page_test_helper(c, "/admin/content/testingquestion/")
        self.admin_page_test_helper(c, "/admin/content/goldenegg/")
        self.admin_page_test_helper(c, "/admin/content/event/")

    def test_core_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/core/")
        self.admin_page_test_helper(c, "/admin/core/class/")
        self.admin_page_test_helper(c, "/admin/core/participantquestionanswer/")
        self.admin_page_test_helper(c, "/admin/core/participant/")

    def test_gamification_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/gamification/")
        self.admin_page_test_helper(c, "/admin/gamification/gamificationbadgetemplate/")
        self.admin_page_test_helper(c, "/admin/gamification/gamificationpointbonus/")
        self.admin_page_test_helper(c, "/admin/gamification/gamificationscenario/")

    def test_organisation_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/organisation/")
        self.admin_page_test_helper(c, "/admin/organisation/course/")
        self.admin_page_test_helper(c, "/admin/organisation/module/")
        self.admin_page_test_helper(c, "/admin/organisation/organisation/")
        self.admin_page_test_helper(c, "/admin/organisation/school/")

    def test_results_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.create_and_answer_questions(2, "_res_w_", datetime.now())
        self.create_and_answer_questions(2, "_res_c_", datetime.now(), True)

        url = "/admin/results/%s" % self.course.id
        self.admin_page_test_helper(c, url)

        resp = c.post(url, data={"state": 1})
        self.assertContains(resp, "Activity")

        resp = c.post(url, data={"state": 2})
        self.assertContains(resp, "q_res_w_0")
        self.assertContains(resp, "q_res_w_1")
        self.assertContains(resp, "q_res_c_0")
        self.assertContains(resp, "q_res_c_1")
        self.assertContains(resp, "( 0% correct )")
        self.assertContains(resp, "( 100% correct )")

        resp = c.post(url, data={"state": 2, "module_filter": self.module.id})
        self.assertContains(resp, "q_res_w_0")
        self.assertContains(resp, "q_res_w_1")
        self.assertContains(resp, "q_res_c_0")
        self.assertContains(resp, "q_res_c_1")
        self.assertContains(resp, "( 0% correct )")
        self.assertContains(resp, "( 100% correct )")

        resp = c.post(url, data={"state": 3})
        self.assertContains(resp, "Class Results")
        self.assertContains(resp, self.classs.name)

    def test_basic_learner_filters(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        url = "/admin/auth/learner/?%s=%s"

        #active filter
        resp = c.get(url % ("acic", "a"))
        self.assertContains(resp, "27123456789")

        lad = self.learner.last_active_date
        self.learner.last_active_date = None
        self.learner.save()

        resp = c.get(url % ("acic", "i"))
        self.assertContains(resp, "27123456789")

        self.learner.last_active_date = lad
        self.learner.save()

        #percentage correct
        resp = c.get(url % ("pc", "0"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "1"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "2"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "3"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "4"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "5"))
        self.assertContains(resp, "Learners")

        # no filter number 6 should render 0's data
        resp = c.get(url % ("pc", "6"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc=0&tf=", "0"))
        self.assertContains(resp, "Learners")

        #percentage completed
        resp = c.get(url % ("pqc", "0"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "1"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "2"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "3"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "4"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "5"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "6"))
        self.assertContains(resp, "Learners")

        #limiting number of results returned
        for i in range(1, 6):
            self.create_learner(
                self.school,
                username="+2712345678%s" % i,
                mobile="+2712345678%s" % i,
                country="country",
                area="Test_Area",
                is_staff=True)
        resp = c.get(url % ("lmt", "0"))
        self.assertContains(resp, "Learners")
