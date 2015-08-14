from celery.bin.celery import control
from django.test import TestCase
from content.models import TestingQuestion, Mathml, SUMit
from content.forms import process_mathml_content, render_mathml, convert_to_tags, convert_to_text
from organisation.models import Course, Module, CourseModuleRel
from mock import patch


class TestContent(TestCase):

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_module(self, name, course, **kwargs):
        module = Module.objects.create(name=name, **kwargs)
        rel = CourseModuleRel.objects.create(course=course, module=module)
        module.save()
        rel.save()
        return module

    def create_test_question(self, name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)

    def setUp(self):
        self.course = self.create_course()
        self.module = self.create_module('module', self.course)
        self.question = self.create_test_question('question', self.module)
        self.fake_mail_msg = ""

    def test_create_test_question(self):
        question_content = "solve this equation <math xmlns='http://www.w3.org/1998/Math/MathML' display='block'>" \
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

        testing_question = self.create_test_question('question2', self.module,
                                                     question_content=question_content,
                                                     answer_content=answer_content)

        #self.assertNotEquals(testing_question.question_content, question_content)
        #self.assertNotEquals(testing_question.answer_content, answer_content)

        content = process_mathml_content(question_content, 0, testing_question.id)

        #does the question content contain the img tag
        self.assertNotEquals(testing_question.question_content, content)

        not_rendered = Mathml.objects.filter(rendered=False).count()
        render_mathml()
        rendered = Mathml.objects.filter(rendered=False).count()

        # check if any not rendered mathml has ben rendered
        self.assertEquals(not_rendered, rendered)

    def test_create_test_question(self):
        question_content = "solve this equation <mml:math xmlns:mml='http://www.w3.org/1998/Math/MathML'>" \
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

        testing_question = self.create_test_question('question222', self.module,
                                                     question_content=question_content,
                                                     answer_content=answer_content)

        #self.assertNotEquals(testing_question.question_content, question_content)
        #self.assertNotEquals(testing_question.answer_content, answer_content)

        content = process_mathml_content(question_content, 0, testing_question.id)

        #does the question content contain the img tag
        self.assertNotEquals(testing_question.question_content, content)

        not_rendered = Mathml.objects.filter(rendered=False).count()
        render_mathml()
        rendered = Mathml.objects.filter(rendered=False).count()

        # check if any not rendered mathml has ben rendered
        self.assertEquals(not_rendered, rendered)

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