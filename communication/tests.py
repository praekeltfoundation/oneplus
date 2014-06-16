from django.contrib.auth import get_user_model
from django.test import TestCase

from communication.models import Message
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
