from datetime import datetime
from auth.models import CustomUser, Learner
from communication.models import SmsQueue
from core.models import Class, Participant
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.test import TestCase, Client
from organisation.models import Organisation, School, Course


class SMSQueueTest(TestCase):
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

    def test_add_sms(self):
        password = "12345"
        admin = self.create_admin("asdf", password, "+27123456789")
        c = Client()
        c.login(username=admin.username, password=password)

        # create a participant in course 1 class 1
        learner_1 = self.create_learner(self.school, mobile="+27987654321", country="country", username="+27987654321")
        self.create_participant(learner_1, self.classs, datejoined=datetime.now())

        # create another class in same course
        c1_class2 = self.create_class("c1_class2", self.course)

        # create a participant in course 1 class 2
        learner_2 = self.create_learner(self.school, mobile="+27147852369", country="country", username="+27147852369")
        self.create_participant(learner_2, c1_class2, datejoined=datetime.now())

        # create a new course and a class
        course2 = self.create_course("course2")
        c2_class1 = self.create_class("c2_class1", course2)

        # create a participant in course 2 class 1
        learner_3 = self.create_learner(self.school, mobile="+27963258741", country="country", username="+27963258741")
        self.create_participant(learner_3, c2_class1, datejoined=datetime.now())

        # create another class in course 2
        c2_class2 = self.create_class("c2_class2", course2)

        # create a participant in course 1 class 2
        learner_4 = self.create_learner(self.school, mobile="+27123654789", country="country", username="+27123654789")
        self.create_participant(learner_4, c2_class2, datejoined=datetime.now())

        # send sms to all course (4 sms, total 4)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': 'all',
                            'to_class': 'all',
                            'users': 'all',
                            'date_sent_0': '2014-05-01',
                            'date_sent_1': '00:00:00',
                            'message': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 4)

        # send sms to course 1 (2 sms, total 6)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': 'all',
                            'users': 'all',
                            'date_sent_0': '2014-06-01',
                            'date_sent_1': '01:00:00',
                            'message': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 6)

        # send sms to course 1 class 1 (1 sms, total 7)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': 'all',
                            'date_sent_0': '2014-07-01',
                            'date_sent_1': '02:00:00',
                            'message': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 7)

        # send sms to course 1 class 1 (1 sms, total 8)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': learner_1.id,
                            'date_sent_0': '2014-07-01',
                            'date_sent_1': '02:00:00',
                            'message': 'message'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 8)

        # send sms to course 1 class 1 (1 sms, total 9)
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'users': learner_1.id,
                            'date_sent_0': '2014-07-01',
                            'date_sent_1': '02:00:00',
                            'message': 'message',
                            '_save': '_save'},
                      follow=True)

        self.assertEquals(resp.status_code, 200)
        count = SmsQueue.objects.all().aggregate(Count('id'))['id__count']
        self.assertEqual(count, 9)
        self.assertContains(resp, "<title>Select Queued Sms to change | OnePlus site admin</title>")

        resp = c.get(reverse('com.add_sms'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>SMS</title>")

        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'date_sent_0': '',
                            'date_sent_1': '',
                            'message': ''},
                      follow=True)
        self.assertContains(resp, 'This field is required')

        # testing _save button
        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': c1_class2.id,
                            'date_sent_0': '1900-01-01',
                            'date_sent_1': 'abc',
                            'message': ''},
                      follow=True)
        self.assertContains(resp, 'This field is required')

        resp = c.post(reverse('com.add_sms'), follow=True)
        self.assertContains(resp, 'This field is required')

    def test_view_sms(self):
        password = "12345"
        admin = self.create_admin("asdf", password, "+27123456789")
        c = Client()
        c.login(username=admin.username, password=password)

        learner_1 = self.create_learner(self.school, mobile="+27987654321", country="country", username="+27987654321")
        self.create_participant(learner_1, self.classs, datejoined=datetime.now())

        resp = c.post(reverse('com.add_sms'),
                      data={'to_course': self.course.id,
                            'to_class': self.classs.id,
                            'users': learner_1.id,
                            'date_sent_0': datetime.now().time(),
                            'date_sent_1': datetime.now().date(),
                            'message': 'message'},
                      follow=True)

        db_sms = SmsQueue.objects.all().first()

        resp = c.get(reverse('com.view_sms', kwargs={'sms': 99}))

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Queued SMS not found")

        resp = c.get(reverse('com.view_sms', kwargs={'sms': db_sms.id}))

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>SMS</title>")

        resp = c.post(reverse('com.view_sms', kwargs={'sms': db_sms.id}), follow=True)

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>SMS</title>")