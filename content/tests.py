from content.models import TestingQuestion, Mathml, SUMit, Event, TestingQuestionOption, EventQuestionRel, \
    EventQuestionAnswer
from content.forms import process_mathml_content, render_mathml, convert_to_tags, convert_to_text, \
    TestingQuestionCreateForm
from organisation.models import Course, Module, CourseModuleRel, School, Organisation
from auth.models import Learner
from core.models import Participant, Class, ParticipantBadgeTemplateRel
from content.tasks import end_event_processing_body

from django.test import TestCase
from datetime import datetime
from mock import patch
from django.conf import settings
import os


class TestContent(TestCase):

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

    def delete_test_question(self, question, **kwargs):
        question.delete()

    def setUp(self):
        self.course = self.create_course()
        self.module = self.create_module('module', self.course)
        self.classs = self.create_class('class name', self.course)
        self.question = self.create_test_question('question', self.module)
        self.fake_mail_msg = ""
        self.organisation = self.create_organisation()
        self.school = self.create_school('school name', self.organisation)
        self.learner = self.create_learner(
            self.school,
            mobile="+27123456789",
            country="country")
        self.participant = self.create_participant(
            self.learner,
            self.classs,
            datejoined=datetime.now()
        )

    def create_test_question_helper(self, q_content, a_content, index):
        old_path = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = "/tmp/"

        question_content = "Please solve the following mess: %s" % q_content
        answer_content = "<div><strong>This is the answer: </strong><div>%s" % a_content

        testing_question = self.create_test_question("question_%d" % index, self.module,
                                                     question_content=question_content,
                                                     answer_content=answer_content)

        content = process_mathml_content(question_content, 0, testing_question.id)

        #does the question content contain the img tag
        self.assertNotEquals(testing_question.question_content, content)

        not_rendered = Mathml.objects.filter(rendered=False, source_id=testing_question.id).count()
        render_mathml()
        rendered = Mathml.objects.filter(rendered=True, source_id=testing_question.id).count()

        # check if any not rendered mathml has been rendered
        self.assertEquals(not_rendered, rendered)

        m = Mathml.objects.filter(source_id=testing_question.id)
        self.assertEquals(m.count(), 1)
        self.assertEquals(m[0].rendered, True)

        # Test extraction
        self.assertEquals(convert_to_tags(m[0].mathml_content), q_content)

        settings.MEDIA_ROOT = old_path

    def test_create_test_question(self):

        # normal mathml content
        question_content = "<math xmlns='http://www.w3.org/1998/Math/MathML' display='block'>" \
                           "<msup>" \
                           "<mi>x</mi>" \
                           "<mn>2</mn>" \
                           "<mo>+</mo>" \
                           "<mi>y</mi>" \
                           "<mn>2</mn>" \
                           "</msup>" \
                           "</math>"

        answer_content = "<math xmlns='http://www.w3.org/1998/Math/MathML' display='block'>" \
                         "<msup>" \
                         "<mi>x</mi>" \
                         "<mn>2</mn>" \
                         "<mo>+</mo>" \
                         "<mi>y</mi>" \
                         "<mn>2</mn>" \
                         "</msup>" \
                         "</math>"

        self.create_test_question_helper(question_content, answer_content, 1)

        # namespaced mathml tags
        question_content = "<mml:math xmlns:mml='http://www.w3.org/1998/Math/MathML'>" \
                           "<mml:msup>" \
                           "<mml:mi>x</mml:mi>" \
                           "<mml:mn>2</mml:mn>" \
                           "<mml:mo>+</mml:mo>" \
                           "<mml:mi>y</mml:mi>" \
                           "<mml:mn>2</mml:mn>" \
                           "</mml:msup>" \
                           "</mml:math>"

        answer_content = "<mml:math xmlns:mml='http://www.w3.org/1998/Math/MathML' display='block'>" \
                         "<mml:msup>" \
                         "<mml:mi>x</mml:mi>" \
                         "<mml:mn>2</mml:mn>" \
                         "<mml:mo>+</mml:mo>" \
                         "<mml:mi>y</mml:mi>" \
                         "<mml:mn>2</mml:mn>" \
                         "</mml:msup>" \
                         "</mml:math>"

        self.create_test_question_helper(question_content, answer_content, 2)

    def test_delete_test_question(self):
        q = self.create_test_question('question?', self.module)
        self.delete_test_question(q)
        self.assertEqual(len(TestingQuestion.objects.filter(name=q.name)), 0, 'Q2 not deleted')

    def test_linebreaks(self):
        content = "<p>heading</p><p>content</p>"

        self.question.question_content = content
        self.question.save()

        self.assertEquals(
            self.question.question_content,
            u'<div>heading<br/>content<br/></div>')

    def test_html_sanitize(self):
        content = "<body><head></head><p><b><strike><img>" \
                  "<a href='/test'>Test</a><strike></b></p></body>"

        self.question.question_content = content
        self.question.save()

        self.assertEquals(
            self.question.question_content,
            u'<div><b><img/><a href="/test">Test</a></b><br/></div>')

    def test_convert_to_tags(self):
        content = ''
        tag_content = ''

        converted_content = convert_to_tags(content)

        self.assertEquals(converted_content, tag_content, "Incorrect tag conversion")

    def test_process_math_content(self):
        testing_question = TestingQuestion.objects.filter(name='question').first()

        mathml_content = "Content without mathml markup"
        expected_output = "Content without mathml markup"
        output = process_mathml_content(mathml_content, '0', testing_question.id)
        self.assertEquals(output, expected_output, "They are not equal")

        mathml_content = "Content with mathml markup <mathxmlns='http://www.w3.org/1998/Math/MathML' display='block'>" \
                         "</math> more text"
        expected_output = "Content with mathml markup <img src='/"
        output = process_mathml_content(mathml_content, '0', testing_question.id)

        if expected_output not in output:
            raise Exception

    def test_convert_to_tags(self):
        content = "text &lt;math&gt;x&lt;/math&gt; more text"
        expected_output = "text <math>x</math> more text"
        output = convert_to_tags(content)
        self.assertEquals(output, expected_output, "They are not equal")

    def test_convert_to_text(self):
        content = "text <math>x</math> more text"
        expected_output = "text &lt;math&gt;x&lt;/math&gt; more text"
        output = convert_to_text(content)
        self.assertEquals(output, expected_output, "They are not equal")

    @patch("content.models.mail_managers")
    def test_sumit_create_questions(self, mocked_mail_manages):
        s = SUMit()
        s.course = self.course
        s.name = "Test"
        q = self.create_test_question(
            'question2',
            self.module,
            difficulty=TestingQuestion.DIFF_EASY,
            state=TestingQuestion.PUBLISHED
        )
        q2 = self.create_test_question(
            'question3',
            self.module,
            difficulty=TestingQuestion.DIFF_NORMAL,
            state=TestingQuestion.PUBLISHED
        )
        q3 = self.create_test_question(
            'question4',
            self.module,
            difficulty=TestingQuestion.DIFF_ADVANCED,
            state=TestingQuestion.PUBLISHED
        )
        s.get_questions()
        mocked_mail_manages.assert_called_once_with(
            subject="Test SUMit! - NOT ENOUGH QUESTIONS",
            message="Test SUMit! does not have enough questions. \nEasy Difficulty requires 14 questions"
                    "\nNormal Difficulty requires 10 questions\nAdvanced Difficulty requires 4 questions",
            fail_silently=False)

    #TODO def test_render_mathml(self):

    def create_eov_event(self):
        return Event.objects.create(
            name="Test Event",
            course=self.course,
            activation_date=datetime(2015, 8, 3, 1, 0, 0),
            deactivation_date=datetime(2015, 8, 9, 23, 59, 59),
            number_sittings=Event.MULTIPLE,
            event_points=10,
            type=Event.ET_EXAM,
        )

    def test_end_of_event_task_no_events(self):
        self.assertEquals(Event.objects.all().count(), 0)

        # Test empty run doesn't crash it
        end_event_processing_body()

    def test_end_of_event_task_event_with_no_answers(self):
        e = self.create_eov_event()
        self.assertEquals(Event.objects.all().count(), 1)

        end_event_processing_body()

        e = Event.objects.get(pk=e.pk)

        # event got processed
        self.assertEquals(e.end_processed, True)

        # check that it doesn't crash
        end_event_processing_body()

    def answer_event_question(self, event, question, question_option, correct, answer_date, participant):
        return EventQuestionAnswer.objects.create(
            event=event,
            participant=participant,
            question=question,
            question_option=question_option,
            correct=correct,
            answer_date=answer_date
        )

    def test_end_of_event_task_event_with_answers(self):
        e = self.create_eov_event()
        self.assertEquals(Event.objects.all().count(), 1)

        q = self.create_test_question(
            'question2',
            self.module,
            difficulty=TestingQuestion.DIFF_EASY,
            state=TestingQuestion.PUBLISHED,
        )

        qo = self.create_test_question_option(name="q2_o1", question=q)

        eqr = EventQuestionRel.objects.create(order=1, event=e, question=q)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=True, answer_date=datetime.now(),
                                   participant=self.participant)

        end_event_processing_body()

        e = Event.objects.get(pk=e.pk)

        # event got processed
        self.assertEquals(e.end_processed, True)

        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        # check that it doesn't crash
        end_event_processing_body()

        # ensure no double awarding took place on the second run
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

    def test_end_of_event_task_event_with_answers_for_multiple_learners_both_awarded(self):
        e = self.create_eov_event()
        self.assertEquals(Event.objects.all().count(), 1)

        self.learner2 = self.create_learner(
            self.school,
            mobile="+27123456781",
            country="country",
            username="+27123456781",
        )

        self.participant2 = self.create_participant(
            self.learner2,
            self.classs,
            datejoined=datetime.now()
        )

        q = self.create_test_question(
            'question3',
            self.module,
            difficulty=TestingQuestion.DIFF_EASY,
            state=TestingQuestion.PUBLISHED,
        )

        qo = self.create_test_question_option(name="q3_o1", question=q)

        eqr = EventQuestionRel.objects.create(order=1, event=e, question=q)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=True, answer_date=datetime.now(),
                                   participant=self.participant)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=True, answer_date=datetime.now(),
                                   participant=self.participant2)

        end_event_processing_body()

        e = Event.objects.get(pk=e.pk)

        # event got processed
        self.assertEquals(e.end_processed, True)

        # participant 1 got awarded the badge
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        # participant 2 got awarded the badge
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant2, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        # check that it doesn't crash
        end_event_processing_body()

        # ensure no double awarding took place on the second run
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant2, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

    def test_end_of_event_task_event_with_answers_for_multiple_learners_first_awarded(self):
        e = self.create_eov_event()
        self.assertEquals(Event.objects.all().count(), 1)

        self.learner2 = self.create_learner(
            self.school,
            mobile="+27123456781",
            country="country",
            username="+27123456781"
        )

        self.participant2 = self.create_participant(
            self.learner2,
            self.classs,
            datejoined=datetime.now()
        )

        q = self.create_test_question(
            'question3',
            self.module,
            difficulty=TestingQuestion.DIFF_EASY,
            state=TestingQuestion.PUBLISHED,
        )

        qo = self.create_test_question_option(name="q3_o1", question=q)

        eqr = EventQuestionRel.objects.create(order=1, event=e, question=q)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=True, answer_date=datetime.now(),
                                   participant=self.participant)
        self.answer_event_question(event=e, question=q, question_option=qo, correct=False, answer_date=datetime.now(),
                                   participant=self.participant2)

        end_event_processing_body()

        e = Event.objects.get(pk=e.pk)

        # event got processed
        self.assertEquals(e.end_processed, True)

        # participant 1 got awarded the badge
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        # participant 2 got awarded the badge
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant2, badgetemplate__name="Exam Champ")

        self.assertEquals(awarded_badge.count(), 0)

        # check that it doesn't crash
        end_event_processing_body()

        # ensure no double awarding took place on the second run
        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, badgetemplate__name="Exam Champ")

        self.assertIsNotNone(awarded_badge)
        self.assertEquals(awarded_badge.count(), 1)
        self.assertEquals(awarded_badge[0].awardcount, 1)

        awarded_badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant2, badgetemplate__name="Exam Champ")

        self.assertEquals(awarded_badge.count(), 0)

    def test_module_questions_order_max(self):
        module = Module.objects.get(name='module')
        form_data = {
            'name': 'Auto Generated',
            'module': module.id,
            'content': 'This is some content.',
            'difficulty': 3,
            'state': 1,
            'points': 5,
            'order': 0,
            'testingquestionoption_set-0-correct': True,
            'testingquestionoption_set-0-content': True,
            'testingquestionoption_set-1-correct': True,
            'testingquestionoption_set-1-content': True,
            'testingquestionoption_set-TOTAL_FORMS': 2}
        self.assertTrue(TestingQuestionCreateForm(form_data), 'Generated form is invalid')
        q1 = TestingQuestionCreateForm(form_data.copy()).save()
        q2 = TestingQuestionCreateForm(form_data.copy()).save()
        q3 = TestingQuestionCreateForm(form_data.copy()).save()
        self.delete_test_question(q2)
        q4 = TestingQuestionCreateForm(form_data.copy()).save()
        self.assertLess(q3.order, q4.order, 'Q3.order: %d; Q4.order: %d' % (q3.order, q4.order))
