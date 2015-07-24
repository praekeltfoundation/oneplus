from datetime import datetime
from auth.models import CustomUser, Learner
from communication.models import Message
from core.models import Class, Participant
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.test import TestCase, Client
from organisation.models import Organisation, School, Course


class MessageTest(TestCase):
    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_school(self, name, organisation, **kwargs):
        return School.objects.create(name=name, organisation=organisation, **kwargs)

    def create_course(self, name="course1", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_admin(self, username, password, mobile):
        return CustomUser.objects.create_superuser(
            username=username,
            email='asdf@example.com',
            password=password,
            mobile=mobile)

    def create_learner(self, school, **kwargs):
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        return Participant.objects.create(learner=learner, classs=classs, **kwargs)

    def setUp(self):
        self.organisation = self.create_organisation()
        self.school = self.create_school("abc", self.organisation)
        self.course = self.create_course()
        self.classs = self.create_class("class1", self.course)

    def test_add_message(self):
        password = "12345"
        admin = self.create_admin("asdf", password, "+27123456789")
        c = Client()
        c.login(username=admin.username, password=password)

        # create a participant in course 1 class 1
        leaner_1 = self.create_learner(self.school, mobile="+27987654321", country="country", username="+27987654321")
        self.create_participant(leaner_1, self.classs, datejoined=datetime.now())

        # create another class in same course
        c1_class2 = self.create_class("c1_class2", self.course)

        # create a participant in course 1 class 2
        leaner_2 = self.create_learner(self.school, mobile="+27147852369", country="country", username="+27147852369")
        self.create_participant(leaner_2, c1_class2, datejoined=datetime.now())

        # create a new course and a class
        course2 = self.create_course("course2")
        c2_class1 = self.create_class("c2_class1", course2)

        # create a participant in course 2 class 1
        leaner_3 = self.create_learner(self.school, mobile="+27963258741", country="country", username="+27963258741")
        self.create_participant(leaner_3, c2_class1, datejoined=datetime.now())

        # create another class in course 2
        c2_class2 = self.create_class("c2_class2", course2)

        # create a participant in course 1 class 2
        leaner_4 = self.create_learner(self.school, mobile="+27123654789", country="country", username="+27123654789")
        self.create_participant(leaner_4, c2_class2, datejoined=datetime.now())

        # test date and content validation errors
        resp = c.post(reverse('com.add_message'),
                      data={'name': '',
                            'course': 'all',
                            'to_class': 'all',
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': '',
                            'publishdate_1': '',
                            'content': ''},
                      follow=True)
        self.assertContains(resp, 'This field is required')

        # test invalid date
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': 'all',
                            'to_class': 'all',
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': 'abc',
                            'publishdate_1': 'abc',
                            'content': 'message'},
                      follow=True)
        self.assertContains(resp, 'Please enter a valid date and time.')

        # test users list, all + user
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': 'all',
                            'users': ["all", "1"],
                            'direction': '1',
                            'publishdate_0': '2014-02-01',
                            'publishdate_1': '01:00:00',
                            'content': 'message'},
                      follow=True)
        self.assertContains(resp, 'Please make a valid learner selection')

        # test no data posted
        resp = c.post(reverse('com.add_message'), follow=True)
        self.assertContains(resp, 'This field is required')

        self.assertEquals(resp.status_code, 200)

        # send message to all course (4 messages, total 4)
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': 'all',
                            'to_class': 'all',
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': '2014-01-01',
                            'publishdate_1': '00:00:00',
                            'content': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 4)

        # send message to course 1 (2 messages, total 6)
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': 'all',
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': '2014-02-01',
                            'publishdate_1': '01:00:00',
                            'content': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 6)

        # send message to course 1 class 1 (1 messages, total 7)
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': 'all',
                            'direction': '1',
                            'publishdate_0': '2014-03-01',
                            'publishdate_1': '02:00:00',
                            'content': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 7)

        # send message to course 1 class 1  learner 1(1 messages, total 8)
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': leaner_1.id,
                            'direction': '1',
                            'publishdate_0': '2014-04-03',
                            'publishdate_1': '03:00:00',
                            'content': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 8)

        # send message to course 1 class 1  learner 1(1 messages, total 9)
        # testing _save button
        resp = c.post(reverse('com.add_message'),
                      data={'name': 'asdf',
                            'course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': leaner_1.id,
                            'direction': '1',
                            'publishdate_0': '2014-04-03',
                            'publishdate_1': '03:00:00',
                            'content': 'message',
                            '_save': "_save"},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = Message.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 9)
        self.assertContains(resp, "<title>Select Message to change | OnePlus site admin</title>")

        resp = c.get(reverse('com.add_message'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>Message</title>")

    def test_view_message(self):
        password = "12345"
        admin = self.create_admin("asdf", password, "+27123456789")
        c = Client()
        c.login(username=admin.username, password=password)

        leaner_1 = self.create_learner(self.school, mobile="+27987654321", country="country", username="+27987654321")
        self.create_participant(leaner_1, self.classs, datejoined=datetime.now())

        c.post(reverse('com.add_message'),
               data={'name': 'asdf',
                     'course': self.course.id,
                     'to_class': self.classs.id,
                     'users': leaner_1.id,
                     'direction': '1',
                     'publishdate_0': '2013-02-01',
                     'publishdate_1': '00:00:00',
                     'content': 'message'},
               follow=True)

        db_msg = Message.objects.all().first()

        resp = c.get(reverse('com.view_message', kwargs={'msg': 99}))

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Message not found")

        resp = c.get(reverse('com.view_message', kwargs={'msg': db_msg.id}))

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>Message</title>")

        resp = c.post(reverse('com.view_message', kwargs={'msg': db_msg.id}), follow=True)

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>Message</title>")