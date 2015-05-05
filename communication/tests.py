# coding: utf-8

from django.contrib.auth import get_user_model
from django.test import TestCase
from communication.models import Message, MessageStatus, ChatMessage, Report, ReportResponse, SmsQueue, Ban, Profanity
from organisation.models import Course, Module, CourseModuleRel
from content.models import TestingQuestion
from core.models import Class
from communication.utils import contains_profanity

from datetime import datetime, timedelta


class TestMessage(TestCase):

    # As you write more tests you'll probably find that you'd want to
    # add these utility functions to a helper class that you can then
    # reuse in different test cases

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_class(self, course, name='class name', **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_user(self, mobile="+27123456789", country="country", **kwargs):
        model_class = get_user_model()
        return model_class.objects.create(
            mobile=mobile, country=country, **kwargs)

    def create_message(self, author, course, **kwargs):
        return Message.objects.create(author=author, course=course, **kwargs)

    def setUp(self):
        self.course = self.create_course()
        self.classs = self.create_class(self.course)
        self.user = self.create_user()

    def test_get_messages(self):
        # unused
        dt1 = datetime.now()
        dt2 = dt1 + timedelta(minutes=5)
        dt3 = dt2 + timedelta(minutes=5)
        self.create_message(
            self.user,
            self.course,
            name="msg1",
            publishdate=dt1
        )
        msg2 = self.create_message(
            self.user,
            self.course,
            name="msg2",
            publishdate=dt2
        )
        msg3 = self.create_message(
            self.user,
            self.course,
            name="msg3",
            publishdate=dt3
        )
        # should return the most recent two in descending order of publishdate
        self.assertEqual(
            [msg3, msg2], Message.get_messages(self.user, self.course, 2))

    def test_unread_msg_count(self):
        msg = self.create_message(
            self.user,
            self.course,
            name="msg2",
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
            self.course,
            name="msg2",
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
            self.course,
            name="msg",
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


class TestSmsQueue(TestCase):
    def create_smsqueue(self, **kwargs):
        return SmsQueue.objects.create(**kwargs)

    def test_created_smsqueue(self):
        sms_queue1 = self.create_smsqueue(msisdn="+27721472583", send_date=datetime.now(), message="Message")

        self.assertEqual(sms_queue1.message, "Message", "Message text not the same")


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

        self.assertIsNone(report.response, "Response should be None")

        #create response to report
        report.create_response("Title", "Question updated.")

        self.assertIsNotNone(report.response, "Response doesn't exist")
        self.assertEquals(report.response.title, "Title", "They are not equal")
        self.assertEquals(report.response.content, "Question updated.", "They are not equal")


class TestReportResponse(TestCase):
    def create_report_response(self, _title, _content, **kwargs):
        return ReportResponse.objects.create(title=_title,
                                             content=_content,
                                             **kwargs)

    def test_created_report_response(self):
        response = self.create_report_response("title", "content")

        self.assertEquals(response.title, "title", "They are not equal")
        self.assertEquals(response.content, "content", "They are equal")


class TestBan(TestCase):
    def create_user(self, mobile="+27123456789", country="country", **kwargs):
        model_class = get_user_model()
        return model_class.objects.create(
            mobile=mobile, country=country, **kwargs)

    def create_ban(self, till_when):
        return Ban.objects.create(
            user=self.user,
            when=datetime.now(),
            till_when=till_when,
            source_type=1,
            source_pk=1
        )

    def setUp(self):
        self.user = self.create_user()

    def test_ban_duration(self):
        today = datetime.now()
        today = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)
        b1tw = today
        b2tw = today + timedelta(days=2)

        ban1 = self.create_ban(b1tw)
        self.assertEquals(ban1.get_duration(), 1)
        ban1.delete()

        ban2 = self.create_ban(b2tw)
        self.assertEquals(ban2.get_duration(), 3)


class TestProfanity(TestCase):
    def test_profanity(self):
        Profanity.objects.create(
            word = 'test'
        )

        self.assertEquals(contains_profanity('foo bar'), False)
        self.assertEquals(contains_profanity('test testees testing'), True)
        self.assertEquals(contains_profanity('Test testees testing'), True)
        self.assertEquals(contains_profanity('TeSt testees TesTing'), True)
        self.assertEquals(contains_profanity('test TesTees testing'), True)