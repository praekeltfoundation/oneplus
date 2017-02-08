# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from auth.models import Learner, CustomUser
from content.models import TestingQuestion, TestingQuestionOption, SUMit, EventQuestionRel, EventParticipantRel, \
    EventQuestionAnswer, SUMitLevel
from core.models import Class, Participant, ParticipantQuestionAnswer
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from gamification.models import GamificationBadgeTemplate, GamificationPointBonus, GamificationScenario
from go_http.tests.test_send import RecordingHandler
from oneplus.models import LearnerState
from organisation.models import Course, Module, CourseModuleRel, Organisation, School


def create_test_question(name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)


def create_learner(school, **kwargs):
    if 'grade' not in kwargs:
        kwargs['grade'] = 'Grade 11'
    return Learner.objects.create(school=school, **kwargs)


def create_module(name, course, **kwargs):
    module = Module.objects.create(name=name, **kwargs)
    rel = CourseModuleRel.objects.create(course=course, module=module)
    module.save()
    rel.save()
    return module


def create_participant(learner, classs, **kwargs):
    participant = Participant.objects.create(
        learner=learner, classs=classs, **kwargs)
    return participant


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


def create_school(name, organisation, **kwargs):
    return School.objects.create(
        name=name, organisation=organisation, **kwargs)


def create_course(name="course name", **kwargs):
    return Course.objects.create(name=name, **kwargs)


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_class(name, course, **kwargs):
    return Class.objects.create(name=name, course=course, **kwargs)


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


def create_sumit(name, course, activation_date, deactivation_date, **kwargs):
    return SUMit.objects.create(name=name, course=course, activation_date=activation_date,
                                deactivation_date=deactivation_date, **kwargs)


class TestReports(TestCase):

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
