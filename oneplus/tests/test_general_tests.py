# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from auth.models import Learner, CustomUser
from communication.models import Message, ChatGroup, ChatMessage, Profanity, Post, PostComment, \
    CoursePostRel
from content.models import TestingQuestion, TestingQuestionOption, Event, SUMit, EventStartPage, EventEndPage, \
    EventSplashPage, EventQuestionRel, EventParticipantRel, EventQuestionAnswer, SUMitLevel
from core.models import Class, Participant, ParticipantQuestionAnswer, Setting
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
from oneplus.templatetags.oneplus_extras import format_option
from oneplus.views import get_week_day
from organisation.models import Course, Module, CourseModuleRel, Organisation, School


def append_query_params(url, params):
    if len(params) < 1:
        return url
    return '%s?%s' % (url, '&'.join([('%s=%s' % (idx, params[idx])) for idx in params.keys()]))


def create_test_question(name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)


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


def create_message(author, course, **kwargs):
    return Message.objects.create(author=author, course=course, **kwargs)


def create_test_question_option(name, question, correct=True):
    return TestingQuestionOption.objects.create(
        name=name, question=question, correct=correct)


def create_test_answer(
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


def create_and_answer_questions(num_questions, module, participant, prefix, date):
    answers = []
    for x in range(0, num_questions):
        # Create a question
        question = create_test_question(
            'q' + prefix + str(x), module)

        question.save()
        option = create_test_question_option(
            'option_' + prefix + str(x),
            question)
        option.save()
        answer = create_test_answer(
            participant=participant,
            question=question,
            option_selected=option,
            answerdate=date
        )
        answer.save()
        answers.append(answer)

    return answers


def create_event(name, course, activation_date, deactivation_date, **kwargs):
    return Event.objects.create(name=name, course=course, activation_date=activation_date,
                                deactivation_date=deactivation_date, **kwargs)


def create_sumit(name, course, activation_date, deactivation_date, **kwargs):
    return SUMit.objects.create(name=name, course=course, activation_date=activation_date,
                                deactivation_date=deactivation_date, **kwargs)


def create_event_start_page(event, header, paragraph):
    return EventStartPage.objects.create(event=event, header=header, paragraph=paragraph)


def create_event_end_page(event, header, paragraph):
    return EventEndPage.objects.create(event=event, header=header, paragraph=paragraph)


def create_event_splash_page(event, order_number, header, paragraph):
    return EventSplashPage.objects.create(event=event, order_number=order_number, header=header,
                                          paragraph=paragraph)


def create_event_question(event, question, order):
    return EventQuestionRel.objects.create(event=event, question=question, order=order)


@override_settings(VUMI_GO_FAKE=True)
class GeneralTests(TestCase):

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

    def test_get_next_question(self):
        create_test_question('question1', self.module, state=3)
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
            create_test_question('question1', self.module, state=3)
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
            event_module = create_module("event_module", self.course, type=2)
            event = create_event("event_name", self.course, datetime.now() - timedelta(days=1),
                                 datetime.now() + timedelta(days=1), number_sittings=2, event_points=5, type=1)
            start_page = create_event_start_page(event, "Test Start Page", "Test Start Page Paragraph")
            end_page = create_event_end_page(event, "Test End Page", "Test Start Page Paragraph")
            question_1 = create_test_question("question_1", event_module, state=3)
            question_option_1 = create_test_question_option("question_1_option", question_1)
            create_event_question(event, question_1, 1)
            question_2 = create_test_question("question_2", event_module, state=3)
            question_option_2 = create_test_question_option("question_2_option", question_2)
            create_event_question(event, question_2, 2)

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
        self.learner.last_active_date = (datetime.now() - timedelta(days=2, hours=4))
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
        self.learner.last_active_date = (datetime.now() - timedelta(days=8, hours=4))
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
        self.learner.last_active_date = (datetime.now() - timedelta(hours=4))
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
        msg = create_message(
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
        msg = create_message(
            self.learner,
            self.course, name="msg",
            publishdate=datetime.now(),
            content='test message'
        )

        resp = self.client.get(reverse('com.inbox_detail', kwargs={'messageid': msg.id}))
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

        self.client.post(
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
        question = create_test_question('question1', self.module, question_content='test question', state=3)
        questionoption = create_test_question_option('questionoption1', question)

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

        self.question = create_test_question(
            'question1',
            self.module,
            question_content='test question')
        self.questionoption = create_test_question_option(
            'questionoption1',
            self.question)

        resp = c.get(
            reverse('learn.preview', kwargs={'questionid': self.question.id}))

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
        option = create_test_question_option("wrong", self.question, False)
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

        self.question = create_test_question('question1', self.module, question_content='test question')
        self.questionoption = create_test_question_option('questionoption1', self.question)

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

        self.question = create_test_question(
            'question1',
            self.module,
            question_content='test question',
            state=3)

        self.questionoption = create_test_question_option(
            'questionoption1',
            self.question)

        resp = c.get(
            reverse('learn.preview.wrong', kwargs={'questionid': self.question.id}))

        self.assertContains(resp, "Next time")

    def test_wrong_view(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        question = create_test_question(
            'question1', self.module,
            question_content='test question',
            state=3)

        create_test_question_option('questionoption1', question)

        questionoption2 = create_test_question_option(
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

        create_participant(learner, self.classs, datejoined=datetime.now())
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
            reverse('auth.autologin', kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('prog.points'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.points'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_ontrack_screen(self):
        self.client.get(
            reverse('auth.autologin', kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('prog.ontrack'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.ontrack'), follow=True)
        self.assertEquals(resp.status_code, 200)

        #more than 10 answered
        create_and_answer_questions(11, self.module, self.participant, "name", datetime.now())
        resp = self.client.get(reverse('prog.ontrack'))
        self.assertEquals(resp.status_code, 200)

    def test_bloglist_screen(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
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
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        resp = self.client.get(reverse('com.bloghero'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('com.bloghero'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_badge_screen(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        resp = self.client.get(reverse('prog.badges'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.badges'), follow=True)
        self.assertEquals(resp.status_code, 200)

    def test_signout_screen(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
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

        question1 = create_test_question(
            'question1',
            self.module,
            question_content='test question')
        option1 = create_test_question_option(
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

        question1 = create_test_question(
            'question1',
            self.module,
            question_content='test question')
        option1 = create_test_question_option(
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
        learner = create_learner(self.school, first_name='John', last_name='Smit', mobile='0791234567',
                                 unique_token='qwerty',
                                 unique_token_expiry=datetime.now() + timedelta(days=30))
        course = create_course('Maths Course')
        module = create_module('Maths Module', course, type=Module.EVENT)
        classs = create_class('A class', course)
        participant = create_participant(learner, classs, datejoined=datetime.now())
        sumit = create_sumit('First Summit', course, datetime.now(), datetime.now() + timedelta(days=2))

        question_option_set = list()
        for i in range(1, 16):
            question = create_test_question('easy_question_%2d' % i, module, difficulty=TestingQuestion.DIFF_EASY,
                                            state=TestingQuestion.PUBLISHED)
            correct_option = create_test_question_option('easy_question_%2d_o_1' % i, question)
            question_option_set.append((question, correct_option))
            EventQuestionRel.objects.create(order=i, event=sumit, question=question)

        for i in range(16, 27):
            question = create_test_question('normal_question_%2d' % i, module,
                                            difficulty=TestingQuestion.DIFF_NORMAL,
                                            state=TestingQuestion.PUBLISHED)
            correct_option = create_test_question_option('normal_question_%2d_o_1' % i, question)
            question_option_set.append((question, correct_option))
            EventQuestionRel.objects.create(order=i-15, event=sumit, question=question)

        for i in range(27, 32):
            question = create_test_question('advanced_question_%2d' % i, module,
                                            difficulty=TestingQuestion.DIFF_ADVANCED,
                                            state=TestingQuestion.PUBLISHED)
            correct_option = create_test_question_option('advanced_question_%2d_o_1' % i, question)
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
        sumit = create_sumit('First Summit', self.course, datetime.now(), datetime.now() + timedelta(days=2))
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

        create_class(name='test class 42', course=self.course)

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

        learner = create_learner(
            self.school,
            username="+27123456999",
            mobile="+2712345699", )

        self.participant = create_participant(
            learner,
            self.classs,
            datejoined=datetime.now())
        available -= 1

        space, number_spaces = space_available()
        self.assertEquals(space, True)
        self.assertEquals(number_spaces, available)

        learner2 = self.learner = create_learner(
            self.school,
            username="+27123456988",
            mobile="+2712345688")

        self.participant = create_participant(
            learner2,
            self.classs,
            datejoined=datetime.now())
        available -= 1

        space, number_spaces = space_available()

        self.assertEquals(space, True)
        self.assertEquals(number_spaces, available)

    def test_participant_required_decorator(self):
        learner = create_learner(
            self.school,
            username="+27987654321",
            mobile="+27987654321",
            country="country",
            area="Test_Area",
            unique_token='cba321',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        participant = create_participant(
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
