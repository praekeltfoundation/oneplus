# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from go_http.tests.test_send import RecordingHandler

from auth.models import Learner, CustomUser
from communication.models import Message, Discussion
from content.models import TestingQuestion, TestingQuestionOption, Event, SUMit, EventStartPage, EventEndPage, \
    EventSplashPage, EventQuestionRel, EventParticipantRel, EventQuestionAnswer
from core.models import Class, Participant, ParticipantQuestionAnswer, ParticipantRedoQuestionAnswer, \
    ParticipantBadgeTemplateRel
from gamification.models import GamificationBadgeTemplate, GamificationPointBonus, GamificationScenario
from oneplus.models import LearnerState
from organisation.models import Course, Module, CourseModuleRel, Organisation, School

from oneplus.tasks import update_perc_correct_answers_worker, reset_learner_states


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


def fake_update_all_perc_correct_answers():
    update_perc_correct_answers_worker('24hr', 1)
    update_perc_correct_answers_worker('48hr', 2)
    update_perc_correct_answers_worker('7days', 7)
    update_perc_correct_answers_worker('32days', 32)


@override_settings(VUMI_GO_FAKE=True)
class ChallengeTest(TestCase):
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

    def test_nextchallenge(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        #no questions
        resp = self.client.get(reverse('learn.next'), follow=True)
        self.assertRedirects(resp, reverse("learn.home"), status_code=302, target_status_code=200)
        self.assertContains(resp, "DIG-IT | WELCOME")

        #with question
        question1 = create_test_question(
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
        self.assertRedirects(resp, reverse("learn.home"))

        #create event
        event = create_event("Test Event", self.course, activation_date=datetime.now() - timedelta(days=1),
                             deactivation_date=datetime.now() + timedelta(days=1))
        start_page = create_event_start_page(event, "Test Start Page", "Test Paragraph")
        event_module = create_module("Event Module", self.course, type=2)

        #create event_session variable
        s = self.client.session
        s["event_session"] = True
        s.save()

        #no event questions
        resp = self.client.get(reverse('learn.event'))
        self.assertRedirects(resp, reverse("learn.home"))

        #add question to event
        question = create_test_question("Event Question", event_module, state=3)
        correct_option = create_test_question_option("question_1_option_1", question)
        incorrect_option = create_test_question_option("question_1_option_2", question, correct=False)
        create_event_question(event, question, 1)

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
        self.assertRedirects(resp, reverse("learn.home"))

    def test_event_wrong(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        s = self.client.session
        s["event_session"] = True
        s.save()

        resp = self.client.get(reverse("learn.event_wrong"))
        self.assertRedirects(resp, reverse("learn.home"))

    def test_sumit(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        #no sumit
        resp = self.client.get(reverse('learn.sumit'))
        self.assertRedirects(resp, reverse("learn.home"))

        resp = self.client.get(reverse('learn.sumit_end_page'))
        self.assertRedirects(resp, reverse("learn.home"))

        resp = self.client.get(reverse('learn.sumit_level_up'))
        self.assertRedirects(resp, reverse("learn.home"))

        resp = self.client.get(reverse('learn.sumit_right'))
        self.assertRedirects(resp, reverse("learn.home"))

        resp = self.client.get(reverse('learn.sumit_wrong'))
        self.assertRedirects(resp, reverse("learn.home"))

        #create event
        sumit_badge = GamificationBadgeTemplate.objects.create(name="SUMit Badge")
        gamification_point = GamificationPointBonus.objects.create(name="Sumit Points", value=10)
        badge = GamificationScenario.objects.create(name="SUMit Scenario", badge=sumit_badge,
                                                    module=self.module, course=self.course, point=gamification_point)
        event = create_sumit("SUMit!", self.course, activation_date=datetime.now() - timedelta(days=1),
                             deactivation_date=datetime.now() + timedelta(days=1), event_points=10, airtime=5,
                             event_badge=badge, type=0)
        start_page = create_event_start_page(event, "Test Start Page", "Test Paragraph")

        resp = self.client.get(reverse('learn.sumit_level_up'))
        self.assertRedirects(resp, reverse("learn.home"))

        #no sumit questions
        resp = self.client.get(reverse('learn.sumit'))
        self.assertRedirects(resp, reverse("learn.home"))

        #add question to sumit
        easy_options = dict()
        for i in range(1, 16):
            question = create_test_question("e_q_%d" % i, self.module, difficulty=2, state=3)
            correct_option = create_test_question_option("e_q_o_%d_c" % i, question)
            incorrect_option = create_test_question_option("e_q_o_%d_i" % i, question, correct=False)
            easy_options['%d' % i] = {'c': correct_option, 'i': incorrect_option}
            create_event_question(event, question, i)

        normal_options = dict()
        for i in range(1, 12):
            question = create_test_question("n_q_%d" % i, self.module, difficulty=3, state=3)
            correct_option = create_test_question_option("n_q_o_%d_c" % i, question)
            incorrect_option = create_test_question_option("n_q_o_%d_i" % i, question, correct=False)
            normal_options['%d' % i] = {'c': correct_option, 'i': incorrect_option}
            create_event_question(event, question, i)

        advanced_options = dict()
        for i in range(1, 6):
            question = create_test_question("a_q_%d" % i, self.module, difficulty=4, state=3)
            correct_option = create_test_question_option("a_q_o_%d_c" % i, question)
            incorrect_option = create_test_question_option("a_q_o_%d_i" % i, question, correct=False)
            advanced_options['%d' % i] = {'c': correct_option, 'i': incorrect_option}
            create_event_question(event, question, i)

        resp = self.client.get(reverse('learn.sumit'))
        self.assertEquals(resp.status_code, 200)

        #no data in post
        resp = self.client.post(reverse('learn.sumit'), follow=True)
        self.assertEquals(resp.status_code, 200)

        #invalid option
        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': 99},
                                follow=True)
        self.assertEquals(resp.status_code, 200)

        #VALID ANSWERS
        count = 1
        points = 0
        self.participant.points = 0
        self.participant.save()

        #valid correct answer
        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': easy_options['%d' % count]['c'].id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "sumit_right")
        _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
        self.assertEquals(_learnerstate.sumit_question, 2)
        points += 1
        participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(participant.points, points)
        count += 1
        #test event right post
        resp = self.client.post(reverse("learn.sumit_right"))
        self.assertEquals(resp.status_code, 200)

        #valid incorrect answer
        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': easy_options['%d' % count]['i'].id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "sumit_wrong")
        participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(participant.points, points)
        _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
        self.assertEquals(_learnerstate.sumit_question, 1)
        count += 1
        #test event wrong post
        resp = self.client.post(reverse("learn.sumit_wrong"))
        self.assertEquals(resp.status_code, 200)

        #correct
        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': easy_options['%d' % count]['c'].id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "sumit_right")
        points += 1
        participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(participant.points, points)
        _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
        self.assertEquals(_learnerstate.sumit_question, 2)
        count += 1

        #correct
        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': easy_options['%d' % count]['c'].id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "sumit_right")
        points += 1
        participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(participant.points, points)
        _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
        self.assertEquals(_learnerstate.sumit_question, 3)
        count += 1

        #incorrect
        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': easy_options['%d' % count]['i'].id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "sumit_wrong")
        participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(participant.points, points)
        _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
        self.assertEquals(_learnerstate.sumit_question, 1)
        count += 1

        #correct
        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': easy_options['%d' % count]['c'].id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "sumit_right")
        points += 1
        participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(participant.points, points)
        _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
        self.assertEquals(_learnerstate.sumit_question, 2)
        count += 1

        #correct
        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': easy_options['%d' % count]['c'].id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "sumit_right")
        points += 1
        participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(participant.points, points)
        _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
        self.assertEquals(_learnerstate.sumit_question, 3)
        count += 1

        #correct
        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': easy_options['%d' % count]['c'].id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "sumit_right")
        points += 1
        participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(participant.points, points)
        _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
        self.assertEquals(_learnerstate.sumit_question, 1)
        self.assertEquals(_learnerstate.sumit_level, 2)
        resp = self.client.get(reverse('learn.sumit_level_up'))
        self.assertEquals(resp.status_code, 200)

        #reset
        EventQuestionAnswer.objects.filter(event=event).delete()
        _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
        _learnerstate.sumit_level = 1
        _learnerstate.sumit_question = 1
        _learnerstate.save()
        self.participant.points = 0
        self.participant.save()
        points = 0
        count = 1
        total_counter = 0

        for i in range(1, 5):
            #Easy Questions
            resp = self.client.post(reverse('learn.sumit'),
                                    data={'answer': easy_options['%d' % count]['c'].id},
                                    follow=True)
            self.assertEquals(resp.status_code, 200)
            self.assertRedirects(resp, "sumit_right")
            points += 1
            participant = Participant.objects.get(id=self.participant.id)
            self.assertEquals(participant.points, points)
            _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
            count += 1
            if count <= 3:
                self.assertEquals(_learnerstate.sumit_level, 1)
            else:
                self.assertEquals(_learnerstate.sumit_level, 2)

            total_counter += 1
            if (total_counter % 3) == 0:
                resp = self.client.get(reverse('learn.sumit_level_up'))
                self.assertEquals(resp.status_code, 200)

        #reset count
        count = 1

        for i in range(1, 7):
            #Normal Questions
            resp = self.client.post(reverse('learn.sumit'),
                                    data={'answer': normal_options['%d' % count]['c'].id},
                                    follow=True)
            self.assertEquals(resp.status_code, 200)
            self.assertRedirects(resp, "sumit_right")
            points += 1
            participant = Participant.objects.get(id=self.participant.id)
            self.assertEquals(participant.points, points)
            _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
            count += 1
            if count <= 2:
                self.assertEquals(_learnerstate.sumit_level, 2)
            elif count <= 5:
                self.assertEquals(_learnerstate.sumit_level, 3)
            else:
                self.assertEquals(_learnerstate.sumit_level, 4)

            total_counter += 1
            if (total_counter % 3) == 0:
                resp = self.client.get(reverse('learn.sumit_level_up'))
                self.assertEquals(resp.status_code, 200)

        #reset count
        count = 1

        #go to end page before all the questions are answered
        resp = self.client.get(reverse('learn.sumit_end_page'))
        self.assertRedirects(resp, reverse("learn.home"))

        for i in range(1, 6):
            #Advanced Questions
            resp = self.client.post(reverse('learn.sumit'),
                                    data={'answer': advanced_options['%d' % count]['c'].id},
                                    follow=True)
            self.assertEquals(resp.status_code, 200)
            self.assertRedirects(resp, "sumit_right")
            points += 1
            participant = Participant.objects.get(id=self.participant.id)
            self.assertEquals(participant.points, points)
            _learnerstate = LearnerState.objects.filter(participant__id=self.participant.id).first()
            count += 1
            if count <= 2:
                self.assertEquals(_learnerstate.sumit_level, 4)
            else:
                self.assertEquals(_learnerstate.sumit_level, 5)

            total_counter += 1
            if (total_counter % 3) == 0:
                resp = self.client.get(reverse('learn.sumit_level_up'))
                self.assertEquals(resp.status_code, 200)

        #go to end page
        resp = self.client.get(reverse('learn.sumit_end_page'))
        self.assertContains(resp, "Congratulations!")
        points += event.event_points
        points += gamification_point.value
        participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(participant.points, points)
        pbtr = ParticipantBadgeTemplateRel.objects.filter(badgetemplate=sumit_badge, scenario=badge,
                                                          participant=self.participant)
        self.assertIsNotNone(pbtr)

        resp = self.client.get(reverse('learn.sumit_end_page'))
        self.assertRedirects(resp, reverse("learn.home"))

        #reset result_recieved
        rel = EventParticipantRel.objects.filter(event=event, participant=self.participant).first()
        rel.results_received = False
        rel.save()

        last_question = EventQuestionAnswer.objects.filter(event=event, participant=self.participant,
                                                           question_option=advanced_options['5']['c']).first().delete()

        resp = self.client.post(reverse('learn.sumit'),
                                data={'answer': advanced_options['5']['i'].id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "sumit_wrong")

        resp = self.client.get(reverse('learn.sumit_end_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'Summit')

        #answered all the question
        resp = self.client.get(reverse('learn.sumit'))
        self.assertRedirects(resp, reverse("learn.home"))

        #reset result_recieved
        rel = EventParticipantRel.objects.filter(event=event, participant=self.participant).first()
        rel.results_received = False
        rel.save()

        _learnerstate.sumit_level = 4
        _learnerstate.save()

        resp = self.client.get(reverse('learn.sumit_end_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'Peak')

        #reset result_recieved
        rel = EventParticipantRel.objects.filter(event=event, participant=self.participant).first()
        rel.results_received = False
        rel.save()

        _learnerstate.sumit_level = 3
        _learnerstate.save()

        resp = self.client.get(reverse('learn.sumit_end_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'Cliffs')

        #reset result_recieved
        rel = EventParticipantRel.objects.filter(event=event, participant=self.participant).first()
        rel.results_received = False
        rel.save()

        _learnerstate.sumit_level = 2
        _learnerstate.save()

        resp = self.client.get(reverse('learn.sumit_end_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'Foothills')

        #reset result_recieved
        rel = EventParticipantRel.objects.filter(event=event, participant=self.participant).first()
        rel.results_received = False
        rel.save()

        _learnerstate.sumit_level = 1
        _learnerstate.save()

        resp = self.client.get(reverse('learn.sumit_end_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'Basecamp')

        # test state reset
        cnt = LearnerState.objects.filter(sumit_question__gt=0).count()
        self.assertEquals(1, cnt)
        reset_learner_states()
        cnt = LearnerState.objects.filter(sumit_question__gt=0).count()
        self.assertEquals(0, cnt)

    def test_redo(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        resp = self.client.get(reverse("learn.redo"))
        self.assertRedirects(resp, reverse("learn.home"))

        for i in range(1, 15):
            question = TestingQuestion.objects.create(name="Question %d" % i, module=self.module)
            correct_option = TestingQuestionOption.objects.create(name="Option %d.1" % i, question=question,
                                                                  correct=True)
            ParticipantQuestionAnswer.objects.create(participant=self.participant, question=question,
                                                     option_selected=correct_option, correct=True)

        question = TestingQuestion.objects.create(name="Question %d" % 15, module=self.module)
        incorrect_option = TestingQuestionOption.objects.create(name="Option %d.1" % 15, question=question,
                                                                correct=False)
        correct_option = TestingQuestionOption.objects.create(name="Option %d.2" % 15, question=question, correct=True)
        ParticipantQuestionAnswer.objects.create(participant=self.participant, question=question,
                                                 option_selected=incorrect_option, correct=False)

        resp = self.client.post(reverse('learn.redo'), follow=True)
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('learn.redo'),
                                data={'answer': 99},
                                follow=True)
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('learn.redo'),
                                data={'answer': correct_option.id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "redo_right")

        resp = self.client.post(reverse("learn.redo_right"))
        self.assertEquals(resp.status_code, 200)
        redo_question = LearnerState.objects.get(participant=self.participant).redo_question
        self.assertContains(resp, "%d point" % (redo_question.points,))

        resp = self.client.post(reverse("learn.redo_right"),
                                data={"comment": "test"},
                                follow=True)

        self.assertEquals(resp.status_code, 200)

        disc = Discussion.objects.all().first()

        resp = self.client.post(
            reverse('learn.redo_right'),
            data={
                'reply': 'test',
                "reply_button": disc.id
            },
            follow=True
        )

        resp = self.client.post(
            reverse('learn.redo_right'),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Discussion.objects.all().count(), 2)

        disc.delete()
        ParticipantRedoQuestionAnswer.objects.filter(participant=self.participant, question=question).delete()

        resp = self.client.post(reverse('learn.redo'),
                                data={'answer': incorrect_option.id},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertRedirects(resp, "redo_wrong")

        resp = self.client.post(reverse("learn.redo_wrong"))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('learn.redo_wrong'),
            data={'comment': 'test'}, follow=True
        )

        self.assertEquals(resp.status_code, 200)

        disc = Discussion.objects.all().first()

        resp = self.client.post(
            reverse('learn.redo_wrong'),
            data={
                'reply': 'test',
                "reply_button": disc.id
            },
            follow=True
        )

        self.assertEquals(resp.status_code, 200)
        self.assertEquals(Discussion.objects.all().count(), 2)

        resp = self.client.post(
            reverse('learn.redo_wrong'),
            data={'page': 1},
            follow=True
        )

        self.assertEquals(resp.status_code, 200)

    def test_redo_counts(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        resp = self.client.get(reverse("learn.redo"))
        self.assertRedirects(resp, reverse("learn.home"))

        questions = {}

        for i in range(1, 15):
            correct = i % 2 == 0
            question = TestingQuestion.objects.create(name="Question %d" % i, module=self.module)
            correct_option = TestingQuestionOption.objects.create(name="Option %d.1" % i, question=question,
                                                                  correct=True)
            incorrect_option = TestingQuestionOption.objects.create(name="Option %d.2" % i, question=question,
                                                                    correct=False)
            ParticipantQuestionAnswer.objects.create(participant=self.participant,
                                                     question=question,
                                                     option_selected=correct_option if correct else incorrect_option,
                                                     correct=correct)
            questions[question.id] = {
                'question_id': question.id,
                'correct_id': correct_option.id,
                'incorrect_id': incorrect_option.id,
                'correct': correct}

        lstate = LearnerState.objects.get(participant_id=self.participant.id)
        incorrect_count = ParticipantQuestionAnswer.objects.filter(correct=False).count()
        redo_correct_count = 0
        for i in range(incorrect_count):
            resp = self.client.get(reverse("learn.redo"), follow=True)
            self.assertContains(
                resp,
                ('Question %d/%d' % (redo_correct_count + 1, incorrect_count)),
                count=1)
            lstate = LearnerState.objects.get(pk=lstate.pk)
            item = questions[lstate.redo_question_id]

            resp = self.client.post(reverse('learn.redo'),
                                    data={'answer': item['incorrect_id']},
                                    follow=True)

            resp = self.client.get(reverse("learn.redo"), follow=True)
            self.assertContains(
                resp,
                ('Question %d/%d' % (redo_correct_count + 1, incorrect_count)),
                count=1)
            lstate = LearnerState.objects.get(pk=lstate.pk)
            item = questions[lstate.redo_question_id]

            resp = self.client.post(reverse('learn.redo'),
                                    data={'answer': item['correct_id']},
                                    follow=True)
            redo_correct_count += 1

        resp = self.client.get(reverse("learn.redo"), follow=True)
        self.assertRedirects(resp, reverse("learn.home"))

    def test_rightanswer(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )
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

        question1 = create_test_question(
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
        self.assertRedirects(resp, reverse("learn.home"))

        #create event
        event = create_event("Test Event", self.course, activation_date=datetime.now() - timedelta(days=1),
                             deactivation_date=datetime.now() + timedelta(days=1), type=1)
        splash_page = create_event_splash_page(event, 1, "Test Splash Page", "Test Paragraph")
        event_module = create_module("Event Module", self.course, type=2)
        question = create_test_question("Event Question", event_module, state=3)
        create_event_question(event, question, 1)

        resp = self.client.get(reverse('learn.event_splash_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, splash_page.header)

        resp = self.client.post(reverse('learn.event_splash_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, splash_page.header)

        EventParticipantRel.objects.create(event=event, participant=self.participant, sitting_number=1)

        resp = self.client.get(reverse('learn.event_splash_page'))
        self.assertRedirects(resp, reverse("learn.home"))

        event.type = 0
        event.save()

        resp = self.client.get(reverse('learn.event_splash_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, splash_page.header)

        resp = self.client.post(reverse('learn.event_splash_page'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, splash_page.header)

    def test_event_start_page(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )

        #no event
        resp = self.client.get(reverse('learn.event_start_page'))
        self.assertRedirects(resp, reverse("learn.home"))

        #create event
        event = create_event("Test Event", self.course, activation_date=datetime.now() - timedelta(days=1),
                             deactivation_date=datetime.now() + timedelta(days=1), type=1)
        start_page = create_event_start_page(event, "Test Start Page", "Test Paragraph")
        event_module = create_module("Event Module", self.course, type=2)
        question = create_test_question("Event Question", event_module, state=3)
        create_event_question(event, question, 1)

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
        self.assertRedirects(resp, reverse("learn.home"))

        #change to multiple sittings
        event.number_sittings = 2
        event.save()

        resp = self.client.post(reverse("learn.event_start_page"),
                                data={"event_start_button": "Get Started"}, follow=True)
        self.assertRedirects(resp, "event")
        event_participant_rel = EventParticipantRel.objects.get(event=event, participant=self.participant)
        self.assertEquals(event_participant_rel.sitting_number, 2)

        event.deactivation_date = datetime.now()
        event.save()

        event = create_sumit("Test SUMit", self.course, activation_date=datetime.now() - timedelta(days=1),
                             deactivation_date=datetime.now() + timedelta(days=1), type=0)
        start_page = create_event_start_page(event, "Test Start Page", "Test Paragraph")
        question = create_test_question("SUMit Question", event_module, state=3, difficulty=2)
        create_event_question(event, question, 1)

        resp = self.client.post(reverse("learn.event_start_page"),
                                data={"event_start_button": "Get Started"}, follow=True)
        self.assertRedirects(resp, "sumit")
        self.assertContains(resp, "SUMit!")

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
        self.assertRedirects(resp, reverse("learn.home"))

        spot_test = GamificationBadgeTemplate.objects.create(name="Spot Test 1")
        badge = GamificationScenario.objects.create(name="Spot Test 1", badge=spot_test, event="SPOT_TEST_1",
                                                    module=self.module, course=self.course)

        event = Event.objects.create(name="Spot Test event", course=self.course, activation_date=datetime.now(),
                                     deactivation_date=datetime.now() + timedelta(days=1), event_points=5, airtime=5,
                                     event_badge=badge, type=Event.ET_SPOT_TEST)
        for i in range(1, 6):
            EventParticipantRel.objects.create(event=event, participant=self.participant, sitting_number=1)
        question = create_test_question("Event question", self.module)
        question_option = create_test_question_option("Option 1", question, True)
        EventQuestionRel.objects.create(event=event, question=question, order=1)
        EventQuestionAnswer.objects.create(event=event, participant=self.participant, question=question,
                                           question_option=question_option, correct=True, answer_date=datetime.now())
        EventEndPage.objects.create(event=event, header="Test End Page", paragraph="Test")

        resp = self.client.get(reverse('learn.event_end_page'))

        pbtr = ParticipantBadgeTemplateRel.objects.filter(badgetemplate=spot_test, scenario=badge,
                                                          participant=self.participant)

        _participant = Participant.objects.get(id=self.participant.id)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(_participant.points, 5)
        self.assertIsNotNone(pbtr)

        event.name = "Exam"
        event.type = 2
        event.save()

        resp = self.client.get(reverse('learn.event_end_page'))

        self.assertEquals(resp.status_code, 200)

    def test_report_question(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token}))

        question = create_test_question(
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
