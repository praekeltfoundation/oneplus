from datetime import datetime, timedelta
from auth.models import Learner
from content.models import TestingQuestion, TestingQuestionOption
from core.models import Class, Participant, ParticipantQuestionAnswer
from django.test import TestCase
from django.test.utils import override_settings
from mock import patch
from oneplus.models import LearnerState
from oneplus.utils import get_today
from organisation.models import Course, Module, CourseModuleRel, Organisation, School


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
        self.assertEquals(week_range[0], datetime(2014, 8, 18).date())

        # End: Friday the 22nd of August
        self.assertEquals(week_range[1], datetime(2014, 8, 23).date())

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
