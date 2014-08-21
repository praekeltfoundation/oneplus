from django.test import TestCase
from datetime import datetime
from auth.models import Learner
from organisation.models import Course, Module, School, Organisation
from core.models import (Participant, Class, ParticipantBadgeTemplateRel,
                         ParticipantQuestionAnswer)
from gamification.models import (GamificationBadgeTemplate,
                                 GamificationPointBonus,
                                 GamificationScenario)
from content.models import TestingQuestion, TestingQuestionOption, TestingBank


class TestMessage(TestCase):

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_module(self, name, course, **kwargs):
        return Module.objects.create(name=name, course=course, **kwargs)

    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_test_question(self, name, bank, **kwargs):
        return TestingQuestion.objects.create(name=name, bank=bank, **kwargs)

    def create_test_question_option(self, name, question, correct=True):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=correct)

    def create_testbank(self, name, module, **kwargs):
        return TestingBank.objects.create(name=name, module=module, **kwargs)

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
        self.testbank = self.create_testbank('test bank', self.module)
        self.badge_template = self.create_badgetemplate()
        self.question = self.create_test_question('q1', self.testbank)
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
                                              bank=self.testbank)

        option2 = self.create_test_question_option(name="option2",
                                                   question=question2,
                                                   correct=False)

        self.participant.answer(self.question, self.option)
        self.participant.answer(question2, option2)

        self.participant.points = 0

        self.participant.recalculate_total_points()
        self.assertEqual(self.participant.points, 1)







