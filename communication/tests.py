# coding: utf-8

from django.contrib.auth import get_user_model
from django.test import TestCase

from communication.models import Message, MessageStatus, ChatMessage, Report, ReportResponse
from organisation.models import Course, Module, CourseModuleRel
from content.models import TestingQuestion

from datetime import datetime


class TestMessage(TestCase):

    # As you write more tests you'll probably find that you'd want to
    # add these utility functions to a helper class that you can then
    # reuse in different test cases

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_user(self, mobile="+27123456789", country="country", **kwargs):
        model_class = get_user_model()
        return model_class.objects.create(
            mobile=mobile, country=country, **kwargs)

    def create_message(self, author, course, **kwargs):
        return Message.objects.create(author=author, course=course, **kwargs)

    def setUp(self):
        self.course = self.create_course()
        self.user = self.create_user()

    def test_get_messages(self):
        # unused
        self.create_message(
            self.user,
            self.course,
            name="msg1",
            publishdate=datetime.now()
        )
        msg2 = self.create_message(
            self.user,
            self.course, name="msg2",
            publishdate=datetime.now()
        )
        msg3 = self.create_message(
            self.user,
            self.course,
            name="msg3",
            publishdate=datetime.now()
        )
        # should return the most recent two in descending order of publishdate
        self.assertEqual(
            [msg3, msg2], Message.get_messages(self.user, self.course, 2))

    def test_unread_msg_count(self):
        msg = self.create_message(
            self.user,
            self.course, name="msg2",
            publishdate=datetime.now()
        )
        msg2 = self.create_message(
            self.user,
            self.course,
            name="msg3",
            publishdate=datetime.now()
        )
        # should return 2 unread messages
        self.assertEqual(
            2, Message.unread_message_count(self.user, self.course))

    def test_view_message(self):
        msg = self.create_message(
            self.user,
            self.course, name="msg2",
            publishdate=datetime.now()
        )

        _status = MessageStatus.objects.create(message=msg, user=self.user)

        # view status is False
        self.assertFalse(_status.view_status)

        msg.view_message(self.user)
        msg.save()

        _status = MessageStatus.objects.get(message=msg)

        # view status is True
        self.assertTrue(_status.view_status)

    def test_hide_message(self):
        msg = self.create_message(
            self.user,
            self.course, name="msg",
            publishdate=datetime.now()
        )

        hide_status = MessageStatus.objects.create(message=msg, user=self.user)

        # hide status is False
        self.assertFalse(hide_status.hidden_status)

        msg.hide_message(self.user)
        msg.save()

        hide_status = MessageStatus.objects.get(message=msg)
        # hide status is True
        self.assertTrue(hide_status.hidden_status)


class TestChatMessage(TestCase):
    def create_chat_message(self, content="", **kwargs):
        return ChatMessage.objects.create(content=content, **kwargs)

    def test_created_message(self):
        msg = self.create_chat_message(content="Ò")
        self.assertEqual(msg.content, 'Ò', "They are not equal")


class TestReport(TestCase):
    def create_user(self, _mobile="+27123456789", _country="country", **kwargs):
        model_class = get_user_model()
        return model_class.objects.create(mobile=_mobile, country=_country, **kwargs)

    def create_course(self, _name="course name", **kwargs):
        return Course.objects.create(name=_name, **kwargs)

    def create_module(self, _course, _name="module name", **kwargs):
        module = Module.objects.create(name=_name, **kwargs)
        rel = CourseModuleRel.objects.create(course=_course, module=module)
        module.save()
        rel.save()
        return module

    def create_question(self, _module, _name="question name", _q_content="2+2", _a_content="4", **kwargs):
        return TestingQuestion.objects.create(name=_name, module=_module, question_content=_q_content,
                                              answer_content=_a_content, **kwargs)

    def setUp(self):
        self.user = self.create_user()
        self.course = self.create_course()
        self.module = self.create_module(self.course)
        self.question = self.create_question(self.module)

    def create_report(self, _issue, _fix, **kwargs):
        return Report.objects.create(user=self.user,
                                     question=self.question,
                                     issue=_issue,
                                     fix=_fix,
                                     **kwargs)

    def test_created_report(self):
        report = self.create_report("There is an error.", "The answer should be 10.")

        self.assertEquals(report.issue, "There is an error.", "They are not equal")
        self.assertEquals(report.fix, "The answer should be 10.", "They are not equal")
        self.assertEquals(report.question.name, "question name", "They are not equal")

        self.assertEquals(report.response, None, "They are not equal")
        #self.assertIsNone(report.response, "Response should be None")

        #create response to report
        report.create_response("Title", "Question updated.")
        report.save()

        self.assertIsNotNone(report.response, "Response doesn't exist")
        #self.assertEquals(report.response, None, "The response doesn't exist.")
        self.assertEquals(report.response.title, "Title", "They are not equal")
        self.assertEquals(report.response.content, "Question updated.", "They are not equal")
        self.assertContains(report.response.publish_date, datetime.now().date(), "The date is not the same")


class TestReportResponse(TestCase):
    def create_report_response(self, _title, _content, **kwargs):
        return ReportResponse.objects.create(title=_title,
                                             content=_content,
                                             publish_date=datetime.now().date(),
                                             **kwargs)

    def test_created_report_response(self):
        response = self.create_report_response("title", "content")

        self.assertEquals(response.title, "title", "They are not equal")
        self.assertEquals(response.content, "content", "They are equal")
        #self.assertContains(str(response.publish_date), str(datetime.now().date()), "The date is not the same")