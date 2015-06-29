from django.db.models import signals
from django.contrib.auth.management import create_permissions
from django.core.management import call_command
from django.test import TestCase
from django.test.runner import DiscoverRunner
from datetime import datetime
from auth.models import Learner
from organisation.models import Course, Module, School, Organisation, CourseModuleRel
from core.models import Participant, Class, ParticipantBadgeTemplateRel, ParticipantQuestionAnswer
from gamification.models import GamificationBadgeTemplate, GamificationPointBonus, GamificationScenario
from content.models import TestingQuestion, TestingQuestionOption
import tablib
from import_export import resources
from auth.resources import LearnerResource
from core.stats import *


class TestRunner(DiscoverRunner):

    def setup_databases(self, **kwargs):
        '''
        syncdb won't create the tables for django.contrib.auth due to
        the custom auth app's migrations. So we have to disconnect
        the create_permissions signal handler in django.contrib.auth until
        its tables have been created (using syncdb --all AFTER migrate).
        '''
        signals.post_syncdb.disconnect(
            dispatch_uid="django.contrib.auth.management.create_permissions"
        )
        config = super(TestRunner, self).setup_databases(**kwargs)
        signals.post_syncdb.connect(
            create_permissions,
            dispatch_uid="django.contrib.auth.management.create_permissions"
        )
        call_command('syncdb', all=True, noinput=True)
        return config


class TestMessage(TestCase):

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_module(self, name, course, **kwargs):
        module = Module.objects.create(name=name, **kwargs)
        rel = CourseModuleRel.objects.create(course=course, module=module)
        module.save()
        rel.save()
        return module

    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_test_question(self, name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)

    def create_test_question_option(self, name, question, correct=True):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=correct)

    def create_school(self, name, organisation, **kwargs):
        return School.objects.create(
            name=name,
            organisation=organisation,
            **kwargs)

    def create_learner(self, school, **kwargs):
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        return Participant.objects.create(
            learner=learner,
            classs=classs,
            **kwargs)

    def create_badgetemplate(self, name='badge template name', **kwargs):
        return GamificationBadgeTemplate.objects.create(name=name, **kwargs)

    def create_pointbonus(self, name='point bonus name', **kwargs):
        return GamificationPointBonus.objects.create(name=name, **kwargs)

    def setUp(self):
        self.course = self.create_course()
        self.module = self.create_module('module name', self.course)
        self.classs = self.create_class('class name', self.course)

        self.organisation = self.create_organisation()
        self.school = self.create_school('school name', self.organisation)
        self.learner = self.create_learner(
            self.school,
            mobile="+27123456789",
            country="country")
        self.badge_template = self.create_badgetemplate()
        self.question = self.create_test_question('q1', self.module)
        self.option = self.create_test_question_option('opt_1', self.question)

        # create point bonus with value 5
        self.pointbonus = self.create_pointbonus(value=5)

        # create scenario
        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='test',
            course=self.course,
            module=self.module,
            point=self.pointbonus,
            badge=self.badge_template
        )
        self.participant = self.create_participant(
            self.learner,
            self.classs,
            datejoined=datetime.now()
        )

    def test_award_scenario(self):

        scenario_no_module = GamificationScenario.objects.create(
            name='event name no module',
            event='event name no module',
            course=self.course,
            module=None,
            point=self.pointbonus,
            badge=self.badge_template
        )
        scenario_no_module.save()

        # participant should have 0 points
        self.assertEquals(0, self.participant.points)

        # award points to participant
        self.participant.award_scenario('event name no module', self.module)
        self.participant.save()

        # participant should have 0 points
        self.assertEquals(0, self.participant.points)

        # check badge was awarded
        b = ParticipantBadgeTemplateRel.objects.get(
            participant=self.participant)
        self.assertTrue(b.awarddate)

    def test_answer_question_correctly(self):

        # participant should have 0 points
        self.assertEquals(0, self.participant.points)

        # award points to participant
        self.participant.answer(self.question, self.option)

        # test points have been awarded
        self.assertEqual(1, self.participant.points)

        # test that the correct ParticipantQuestionAnswer
        answer = ParticipantQuestionAnswer.objects.filter(
            participant=self.participant).first()
        self.assertNotEqual(answer, None)
        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.option_selected, self.option)
        self.assertEqual(answer.correct, self.option.correct)

        self.participant.save()

    def test_answer_question_incorrectly(self):
        # Set option to NOT correct
        self.option.correct = False

        # participant should have 0 points
        self.assertEquals(0, self.participant.points)

        # Answer question incorrectly
        self.participant.answer(self.question, self.option)

        # No test points have been awarded
        self.assertEqual(0, self.participant.points)

        self.participant.save()

    def test_get_scenarios_hierarchy(self):
        event = "test"

        # create scenario
        self.scenario_no_module = GamificationScenario.objects.create(
            name='scenario name no module',
            event='test',
            course=self.course,
            module=None,
            point=self.pointbonus,
            badge=self.badge_template
        )
        self.scenario_no_module.save()

        scenarios = self.participant.get_scenarios(event, self.module)
        self.assertEqual(scenarios.first(), self.scenario)

    def test_recalculate_points_only_right(self):
        question2 = self.create_test_question(name="testquestion2",
                                              module=self.module)

        option2 = self.create_test_question_option(name="option2",
                                                   question=question2,
                                                   correct=False)

        self.participant.answer(self.question, self.option)
        self.participant.answer(question2, option2)

        self.participant.points = 0

        self.participant.recalculate_total_points()
        self.assertEqual(self.participant.points, 1)

    def test_learner_import_all_strings(self):
        learner_resource = LearnerResource()
        dataset = tablib.Dataset(
            [
                '',
                '821010002',
                'BAR',
                'FOO',
                '',
                '821010002',
                'Test High School',
                'rsa',
                '',
                'pta',
                '0',
                '0',
                '0',
                '0',
                'class name'],
            headers=[
                'id',
                'username',
                'first_name',
                'last_name',
                'email',
                'mobile',
                'school',
                'country',
                'area',
                'city',
                'optin_sms',
                'optin_email',
                'completed_questions',
                'percentage_correct',
                'class'])
        result = learner_resource.import_data(dataset, dry_run=True)

        if result.has_errors():
            for err in result.row_errors():
                print err

        self.assertEquals(result.has_errors(), False)
        result = learner_resource.import_data(dataset, dry_run=False)
        self.assertEquals(result.has_errors(), False)

        learner = Learner.objects.select_related().filter(username='821010002').first()
        self.assertEquals(learner.username, '821010002')
        self.assertEquals(learner.mobile, '821010002')
        self.assertEquals(learner.school.name, 'Test High School')

    def test_learner_import_float_mobile(self):
        # simulate float numberical values from excel imports
        learner_resource = LearnerResource()
        dataset = tablib.Dataset(
            [
                '',
                float(821010003),
                'BAR',
                'FOO',
                '',
                float(821010003),
                'Test High School',
                'rsa',
                '',
                'pta',
                float(0),
                float(0),
                float(0),
                float(0),
                'class name'],
            headers=[
                'id',
                'username',
                'first_name',
                'last_name',
                'email',
                'mobile',
                'school',
                'country',
                'area',
                'city',
                'optin_sms',
                'optin_email',
                'completed_questions',
                'percentage_correct',
                'class'])
        result = learner_resource.import_data(dataset, dry_run=True)

        if result.has_errors():
            for err in result.row_errors():
                print err

        self.assertEquals(result.has_errors(), False)
        result = learner_resource.import_data(dataset, dry_run=False)
        self.assertEquals(result.has_errors(), False)

        learner = Learner.objects.select_related().filter(username='821010003').first()
        self.assertEquals(learner.username, '821010003')
        self.assertEquals(learner.mobile, '821010003')
        self.assertEquals(learner.school.name, 'Test High School')

    def test_registered_count(self):
        # setup creates 1
        count = participants_registered_last_x_hours(hours=24)

        self.assertEquals(count, 1)

        # create another
        learner_1 = self.create_learner(
            self.school,
            mobile="+27123456788",
            country="country",
            username="+27123456788")

        self.create_participant(
            learner=learner_1,
            classs=self.classs,
            datejoined=datetime.now()
        )

        count = participants_registered_last_x_hours(hours=24)

        self.assertEquals(count, 2)

        # create another but older than 24h
        learner_2 = self.create_learner(
            self.school,
            mobile="+27123456787",
            country="country",
            username="+27123456787")

        self.create_participant(
            learner=learner_2,
            classs=self.classs,
            datejoined=datetime.now() - timedelta(days=2)
        )

        count = participants_registered_last_x_hours(hours=24)

        self.assertEquals(count, 2)

        count = participants_registered_last_x_hours(hours=49)

        self.assertEquals(count, 3)

    def test_answered_in_last_x_hours(self):
        count = questions_answered_in_last_x_hours(hours=24)
        self.assertEquals(count, 0)

        self.participant.answer(question=self.question, option=self.option)
        count = questions_answered_in_last_x_hours(hours=24)
        self.assertEquals(count, 1)

        # adjust the answer date
        qa = ParticipantQuestionAnswer.objects.all()[0]
        qa.answerdate = datetime.now() - timedelta(days=2)
        qa.save()

        count = questions_answered_in_last_x_hours(hours=24)
        self.assertEquals(count, 0)

    def test_answered_correctly_in_last_x_hours(self):
        count = percentage_questions_answered_correctly_in_last_x_hours(hours=24)
        count2 = questions_answered_correctly_in_last_x_hours(hours=24)
        self.assertEquals(count, 0)
        self.assertEquals(count2, 0)

        self.participant.answer(question=self.question, option=self.option)
        count = percentage_questions_answered_correctly_in_last_x_hours(hours=24)
        count2 = questions_answered_correctly_in_last_x_hours(hours=24)
        self.assertEquals(count, 100)
        self.assertEquals(count2, 1)

        self.option.correct = False
        self.participant.answer(question=self.question, option=self.option)
        count = percentage_questions_answered_correctly_in_last_x_hours(hours=24)
        count2 = questions_answered_correctly_in_last_x_hours(hours=24)
        self.assertEquals(count, 50)
        self.assertEquals(count2, 1)

        # adjust the incorrect answer's date
        qa = ParticipantQuestionAnswer.objects.all()[1]
        qa.answerdate = datetime.now() - timedelta(days=2)
        qa.save()

        count = percentage_questions_answered_correctly_in_last_x_hours(hours=24)
        self.assertEquals(count, 100)

    def test_question_answered(self):
        count = question_answered(self.question)
        self.assertEquals(count, 0)

        self.participant.answer(question=self.question, option=self.option)
        count = question_answered(self.question)
        self.assertEqual(count, 1)

    def test_question_answered_correctly(self):
        count = question_answered_correctly(self.question)
        count2 = percentage_question_answered_correctly(self.question)
        self.assertEqual(count, 0)
        self.assertEqual(count2, 0)

        self.participant.answer(question=self.question, option=self.option)
        count = question_answered_correctly(self.question)
        count2 = percentage_question_answered_correctly(self.question)
        self.assertEqual(count, 1)
        self.assertEqual(count2, 100)

        self.option.correct = False
        self.participant.answer(question=self.question, option=self.option)
        count = question_answered_correctly(self.question)
        count2 = percentage_question_answered_correctly(self.question)
        self.assertEqual(count, 1)
        self.assertEqual(count2, 50)