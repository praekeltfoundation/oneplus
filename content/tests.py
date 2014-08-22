from django.test import TestCase
from content.models import TestingQuestion, TestingBank
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

    def create_testing_bank(self, name, module, **kwargs):
        return TestingBank.objects.create(name=name, module=module, **kwargs)

    def create_test_question(self, name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)

    def setUp(self):
        self.course = self.create_course()
        self.module = self.create_module('module', self.course)
        self.question = self.create_test_question('question', self.module)

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
