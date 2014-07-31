from django.contrib.auth import get_user_model
from django.test import TestCase

from communication.models import Message, MessageStatus
from organisation.models import Course

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
