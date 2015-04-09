from django.test import TestCase
from content.models import TestingQuestion
from content.forms import render_mathml
from organisation.models import Course, Module, CourseModuleRel


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

        self.assertNotEquals(testing_question.question_content, question_content)
        self.assertNotEquals(testing_question.answer_content, answer_content)
        render_mathml()

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