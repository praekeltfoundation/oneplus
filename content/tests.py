from django.test import TestCase
from content.models import TestingQuestion, TestingBank
from organisation.models import Course, Module


class TestContent(TestCase):

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_module(self, name, course, **kwargs):
        return Module.objects.create(name=name, course=course, **kwargs)

    def create_testing_bank(self, name, module, **kwargs):
        return TestingBank.objects.create(name=name, module=module, **kwargs)

    def create_test_question(self, name, bank, **kwargs):
        return TestingQuestion.objects.create(name=name, bank=bank, **kwargs)

    def setUp(self):
        self.course = self.create_course()
        self.module = self.create_module('module', self.course)
        self.testbank = self.create_testing_bank('testbank', self.module)
        self.question = self.create_test_question('question', self.testbank)

    def test_html_sanitize(self):
        content = "<body><head></head><p><b><strike><img>" \
                  "<a href='/test'>Test</a><strike></b></p></body>"

        self.question.question_content = content
        self.question.save()

        self.assertEquals(
            self.question.question_content,
            '<div style="vertical-align:middle;'
            'display:inline-block;width:80%"><b>'
            '<img style="vertical-align:middle"/>'
            '<a href="/test">Test</a></b></div>')
