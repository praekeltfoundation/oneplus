# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from auth.models import Learner
from content.models import TestingQuestion, TestingQuestionOption
from core.models import Participant, ParticipantQuestionAnswer, Class
from django.test import TestCase
from mock import patch
from organisation.models import Module, CourseModuleRel, School, Course, Organisation
from oneplus.models import LearnerState


def create_test_question(name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)


def create_learner(school, **kwargs):
    if 'grade' not in kwargs:
        kwargs['grade'] = 'Grade 11'
    if 'terms_accept' not in kwargs:
            kwargs['terms_accept'] = True
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


def create_school(name, organisation, **kwargs):
    return School.objects.create(
        name=name, organisation=organisation, **kwargs)


def create_course(name="course name", **kwargs):
    return Course.objects.create(name=name, **kwargs)


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_class(name, course, **kwargs):
    return Class.objects.create(name=name, course=course, **kwargs)


class TestTraining(TestCase):

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
            self.learner,
            self.classs,
            datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = create_module('module name', self.course)

    @patch.object(LearnerState, 'today')
    def test_training_sunday(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 20, 0, 0, 0)

        question1 = create_test_question('question1', self.module, question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        self.assertEquals(learnerstate.get_total_questions(), 15)

    @patch.object(LearnerState, 'today')
    def test_training_saturday(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 19, 0, 0, 0)

        question1 = create_test_question('question1', self.module, question_content='test question')

        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        self.assertEquals(learnerstate.get_total_questions(), 15)

    @patch.object(LearnerState, 'today')
    def test_monday_first_week_no_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 21, 0, 0, 0)

        question1 = create_test_question('question1', self.module, question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_monday_first_week_with_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 21, 0, 0, 0)

        create_and_answer_questions(
            3,
            self.module,
            self.participant,
            'sunday',
            datetime(2014, 7, 20, 1, 1, 1))

        question1 = create_test_question('question1', self.module, question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_tuesday_with_monday(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 22, 1, 1, 1)

        create_and_answer_questions(
            3,
            self.module,
            self.participant,
            'sunday',
            datetime(2014, 7, 21, 1, 1, 1))

        question1 = create_test_question('question1', self.module, question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_miss_a_day_during_week(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 22, 0, 0, 0)

        question1 = create_test_question('question1', self.module, question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 6)

    @patch.object(LearnerState, 'today')
    def test_miss_multiple_days_during_week(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 23, 0, 0, 0)
        question1 = create_test_question('question1', self.module, question_content='test question')
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
        answers = create_and_answer_questions(
            2,
            self.module,
            self.participant,
            'monday',
            datetime(2014, 7, 21, 1, 1, 1))

        question1 = create_test_question('question1', self.module, question_content='test question')
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

        create_and_answer_questions(3, self.module, self.participant, 'monday', datetime(2014, 7, 21, 1, 1, 1))
        create_and_answer_questions(3, self.module, self.participant, 'tuesday', datetime(2014, 7, 22, 1, 1, 1))
        create_and_answer_questions(3, self.module, self.participant, 'wednesday', datetime(2014, 7, 23, 1, 1, 1))
        create_and_answer_questions(3, self.module, self.participant, 'thursday', datetime(2014, 7, 24, 1, 1, 1))

        question1 = create_test_question('question1', self.module, question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_miss_all_days_till_weekend_except_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 26, 0, 0, 0)

        question1 = create_test_question('question1', self.module, question_content='test question')
        create_and_answer_questions(3, self.module, self.participant, 'training', datetime(2014, 7, 20, 1, 1, 1))
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

        question1 = create_test_question('question1', self.module, question_content='test question')

        # Answered 3 questions at training on Sunday the 20th
        create_and_answer_questions(3, self.module, self.participant, 'training', datetime(2014, 7, 20, 1, 1, 1))
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, "today")
    def test_saturday_no_questions_not_training(self, mock_get_today):
        learner = self.learner = create_learner(self.school,
                                                username="+27123456999",
                                                mobile="+2712345699",
                                                country="country",
                                                area="Test_Area",
                                                unique_token='abc1233',
                                                unique_token_expiry=datetime.now() + timedelta(days=30),
                                                is_staff=True)
        self.participant = create_participant(
            learner, self.classs,
            datejoined=datetime(2014, 8, 22, 0, 0, 0))

        mock_get_today.return_value = datetime(2014, 8, 23, 0, 0)

        # Create question
        question1 = create_test_question('q1', self.module)

        # Create and answer 2 other questions earlier in the day
        create_and_answer_questions(2, self.module, self.participant, 'training',  datetime(2014, 8, 23, 1, 22, 0))

        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        self.assertEquals(learnerstate.get_total_questions(), 15)
        self.assertEquals(learnerstate.get_num_questions_answered_today(), 2)
