from datetime import datetime
from auth.models import CustomUser, Learner
from communication.models import SmsQueue
from core.models import Class, Participant
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.test import TestCase, Client
from django.utils import timezone
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
        if 'terms_accept' not in kwargs:
            kwargs['terms_accept'] = True
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        return Participant.objects.create(learner=learner, classs=classs, **kwargs)

    def setUp(self):
        self.organisation = self.create_organisation()
        self.school = self.create_school("abc", self.organisation)
        self.course = self.create_course()
        self.classs = self.create_class("class1", self.course)

        self.admin_user_password = 'mypassword'
        self.admin_user = CustomUser.objects.create_superuser(
            username='asdf33',
            email='asdf33@example.com',
            password=self.admin_user_password,
            mobile='+27111111133')

    def test_get_users(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        learner = self.create_learner(self.school, mobile='+27123456789', username='+27123456789')
        participant = self.create_participant(learner, classs=self.classs, datejoined=timezone.now())


        resp = c.get('/users/?class=all')
        self.assertContains(resp, '"name": "+27123456789"')

        resp = c.get('/users/?class=%s' % self.classs.id)
        self.assertContains(resp, '"name": "+27123456789"')

        resp = c.get('/users/?class=abc')
        self.assertEquals(resp.status_code, 200)

        resp = c.get('/users/?class=%s' % 99)
        self.assertEquals(resp.status_code, 200)

    def test_add_sms(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

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
        self.assertContains(resp, "<title>Select Queued Sms to change | dig-it site admin</title>")

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

    def test_add_sms_2(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        # empty request
        old_count = SmsQueue.objects.all().count()
        resp = c.post(reverse('com.add_sms'), {})
        self.assertEqual(resp.status_code, 200)
        new_count = SmsQueue.objects.all().count()
        self.assertEqual(new_count, old_count)

        # send to all, single learner
        old_count = SmsQueue.objects.all().count()
        resp = c.post(reverse('com.add_sms'), {
            'users': 'all',
            'to_class': 'all',
            'to_course': 'all',
            'message': 'Ceci n\'est pas une message.',
            'date_sent_0': str(timezone.now().date()),
            'date_sent_1': str(timezone.now().time())})
        self.assertEqual(resp.status_code, 302)
        new_count = SmsQueue.objects.all().count()
        self.assertEqual(new_count, old_count + Learner.objects.all().count())

        # send to all learners in class
        num_learn_gen = 16
        class_2 = self.create_class('Wrong Class', self.course)
        for i in xrange(num_learn_gen):
            l = self.create_learner(
                self.school,
                first_name='Learner %d' % (i,),
                username=('learn_%d' % (i,)),
                mobile=('082564%4.0d' % (i,)))
            p = self.create_participant(
                l,
                self.classs if i % 2 == 0 else class_2,
                datejoined=timezone.now())
        old_count = SmsQueue.objects.all().count()
        resp = c.post(reverse('com.add_sms'), {
            'users': 'all',
            'to_class': self.classs.id,
            'to_course': 'all',
            'message': 'Ceci n\'est pas une message.',
            'date_sent_0': str(timezone.now().date()),
            'date_sent_1': str(timezone.now().time())})
        self.assertEqual(resp.status_code, 302)
        new_count = SmsQueue.objects.all().count()
        self.assertEqual(
            new_count,
            old_count + Learner.objects.filter(participant__classs_id=self.classs.id).distinct('id').count())

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
