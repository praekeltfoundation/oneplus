# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from auth.models import Learner, CustomUser
from communication.models import Post, PostComment, CoursePostRel
from content.models import TestingQuestion, TestingQuestionOption, Event, EventStartPage, EventEndPage, EventQuestionRel
from core.models import Class, Participant, ParticipantQuestionAnswer, Setting
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.test import TestCase, Client
from django.test.utils import override_settings
from gamification.models import GamificationBadgeTemplate, GamificationScenario
from go_http.tests.test_send import RecordingHandler
from mock import patch
from oneplus.auth_views import space_available
from oneplus.models import LearnerState
from oneplus.views import get_week_day
from organisation.models import Course, Module, CourseModuleRel, Organisation, School
from django.conf import settings


def create_test_question(name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)


def create_learner(school, **kwargs):
    if 'grade' not in kwargs:
        kwargs['grade'] = 'Grade 11'
    return Learner.objects.create(school=school, **kwargs)


def create_participant(learner, classs, **kwargs):
    participant = Participant.objects.create(
        learner=learner, classs=classs, **kwargs)
    return participant


def create_test_question_option(name, question, correct=True):
    return TestingQuestionOption.objects.create(
        name=name, question=question, correct=correct)


def create_test_answer(
        participant,
        question,
        option_selected,
        answerdate):
    return ParticipantQuestionAnswer.objects.create(
        participant=participant,
        question=question,
        option_selected=option_selected,
        answerdate=answerdate,
        correct=False
    )


def create_school(name, organisation, **kwargs):
    return School.objects.create(
        name=name, organisation=organisation, **kwargs)


def create_course(name="course name", **kwargs):
    return Course.objects.create(name=name, **kwargs)


def create_class(name, course, **kwargs):
    return Class.objects.create(name=name, course=course, **kwargs)


def create_module(name, course, **kwargs):
    module = Module.objects.create(name=name, **kwargs)
    rel = CourseModuleRel.objects.create(course=course, module=module)
    module.save()
    rel.save()
    return module


def create_badgetemplate(name='badge template name', **kwargs):
    return GamificationBadgeTemplate.objects.create(
        name=name,
        image="none",
        **kwargs)


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


@override_settings(VUMI_GO_FAKE=True)
class TestSignUp(TestCase):
    def setUp(self):
        self.course = create_course()
        self.classs = create_class('class name', self.course)
        self.organisation = create_organisation()
        self.school = create_school('school name', self.organisation)
        self.learner = create_learner(
            self.school,
            username="+27123456789",
            mobile="+27123456789",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        self.participant = create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = create_module('module name', self.course)
        self.badge_template = create_badgetemplate()

        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='1_CORRECT',
            course=self.course,
            module=self.module,
            badge=self.badge_template
        )
        self.outgoing_vumi_text = []
        self.outgoing_vumi_metrics = []
        self.handler = RecordingHandler()
        logger = logging.getLogger('DEBUG')
        logger.setLevel(logging.INFO)
        logger.addHandler(self.handler)

        self.admin_user_password = 'mypassword'
        self.admin_user = CustomUser.objects.create_superuser(
            username='asdf33',
            email='asdf33@example.com',
            password=self.admin_user_password,
            mobile='+27111111133')

    # @override_settings(GRADE_11_COURSE_NAME='Grade 11 Course')
    def test_signup_return(self):
        with patch("oneplus.auth_views.mail_managers") as mock_mail_managers:
            # test not logged in
            resp = self.client.get(reverse('auth.return_signup'))
            self.assertRedirects(resp, reverse('auth.login'))
            resp = self.client.get(reverse('auth.return_signup_school_confirm'))
            self.assertRedirects(resp, reverse('auth.login'))

            # test user not enrolled
            self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
            resp = self.client.get(reverse('auth.return_signup'))
            self.assertRedirects(resp, reverse('learn.home'))
            resp = self.client.get(reverse('auth.return_signup_school_confirm'))
            self.assertRedirects(resp, reverse('learn.home'))

            self.learner.first_name = 'Blarg'
            self.learner.last_name = 'Honk'
            self.learner.enrolled = '0'
            self.learner.save()

            self.course.name = settings.GRADE_11_COURSE_NAME
            self.course.save()

            resp = self.client.get(reverse('learn.home'), folow=True)
            self.assertRedirects(resp, reverse('auth.return_signup'))

            # plain get
            resp = self.client.get(reverse('auth.return_signup'), folow=True)
            self.assertContains(resp, 'Hello, %s.' % self.learner.first_name, count=1)

            # no data given
            resp = self.client.post(reverse('auth.return_signup'),
                                    data={},
                                    follow=True)
            self.assertContains(resp, "This must be completed", count=3)
            self.assertContains(resp, 'Hello, %s' % self.learner.first_name, count=1)

            # correct data given (p1)
            resp = self.client.post(reverse('auth.return_signup'),
                                    data={
                                        'grade': 'Grade 11',
                                        'province': 'Gauteng',
                                        'school_dirty': self.school.name},
                                    follow=True)
            self.assertContains(resp, self.school.name)

            # test ElasticSearch succeeds
            with patch("oneplus.auth_views.SearchQuerySet") as MockSearchSet:
                # non-empty search result
                MockSearchSet().filter().values.return_value = [{'pk': 1, 'name': 'Blargity School'}]
                resp = self.client.post(reverse('auth.return_signup'),
                                        data={
                                            'province': 'Gauteng',
                                            'grade': 'Grade 11',
                                            'school_dirty': 'blarg'},
                                        follow=True)
                MockSearchSet.assert_called()
                self.assertContains(resp, 'Blargity School')
                MockSearchSet.clear()

            # get redirect (p2)
            resp = self.client.get(reverse('auth.return_signup_school_confirm'), follow=True)
            self.assertRedirects(resp, reverse('auth.return_signup'))
            self.assertContains(resp, 'Hello, %s' % self.learner.first_name, count=1)

            # incomplete data given (p2)
            resp = self.client.post(reverse('auth.return_signup_school_confirm'),
                                    data={},
                                    follow=True)
            self.assertContains(resp, "This must be completed", count=3)

            # incorrect data given (p2)
            resp = self.client.post(reverse('auth.return_signup_school_confirm'),
                                    data={
                                        'grade': 'Grade 11',
                                        'province': 'Gauteng',
                                        'school': 'other'},
                                    follow=True)
            self.assertContains(resp, 'No such school')

            # correct data given (p2)
            resp = self.client.post(reverse('auth.return_signup_school_confirm'),
                                    data={
                                        'grade': 'Grade 11',
                                        'province': 'Gauteng',
                                        'school': self.school.id},
                                    follow=True)
            self.assertRedirects(resp, reverse('learn.home'))
            self.participant = Participant.objects.get(pk=self.participant.pk)
            self.assertFalse(self.participant.is_active)
            self.assertNotEqual(Participant.objects.get(learner=self.learner, is_active=True).pk, self.participant.pk)
            self.assertEqual(self.learner.enrolled, "0")

    def test_signup(self):
        learner = create_learner(
            self.school,
            username="+27123456999",
            mobile="+2712345699", )

        self.participant = create_participant(
            learner,
            self.classs,
            datejoined=datetime.now())

        resp = self.client.get(reverse('auth.signup'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('auth.signup'), data={'yes': "Yes, please sign me up!"}, follow=True)
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('auth.signup'), data={'no': "Not interested right now"}, follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "<title>DIG-IT | HELLO</title>")

    def test_signup_form(self):
        with patch("oneplus.auth_views.mail_managers") as mock_mail_managers:
            self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
            province_school = School.objects.get(name="Open School")
            self.course.name = settings.GRADE_10_COURSE_NAME
            self.course.save()
            promaths_school = create_school(
                "ProMaths School",
                province_school.organisation,
                open_type=School.OT_CLOSED)

            promaths_class = create_class("ProMaths Class", self.course)
            resp = self.client.get(reverse('auth.signup_form'))
            self.assertEqual(resp.status_code, 200)

            # no data given
            resp = self.client.post(reverse('auth.signup_form'),
                                    data={},
                                    follow=True)
            self.assertContains(resp, "This must be completed", count=3)

            # invalid cellphone, grade and province
            resp = self.client.post(reverse('auth.signup_form'),
                                    data={
                                        'first_name': self.learner.first_name,
                                        'surname': self.learner.last_name,
                                        'cellphone': '12345',
                                        'enrolled': 0,
                                    },
                                    follow=True)
            self.assertContains(resp, "Enter a valid cellphone number")

            # registered cellphone
            resp = self.client.post(reverse('auth.signup_form'),
                                    data={
                                        'first_name': "Bob",
                                        'surname': "Bobby",
                                        'cellphone': self.learner.mobile,
                                        'grade': 'Grade 10',
                                        'province': 'Gauteng',
                                        'enrolled': 0
                                    },
                                    follow=True)
            self.assertContains(resp, "This number has already been registered.")

            # valid - enrolled
            resp = self.client.post(reverse('auth.signup_form'),
                                    data={
                                        'first_name': "Bob",
                                        'surname': "Bobby",
                                        'cellphone': '0729876543',
                                        'province': 'Gauteng',
                                        'grade': 'Grade 10',
                                        'enrolled': 0,
                                    },
                                    follow=True)
            self.assertContains(resp, 'Bob')
            self.assertContains(resp, 'Bobby')
            self.assertContains(resp, '0729876543')
            self.assertContains(resp, 'Gauteng')
            self.assertContains(resp, 'Grade 10')
            self.assertContains(resp, '0')

            #get request
            resp = self.client.get(reverse('auth.signup_form_normal'), follow=True)
            self.assertContains(resp, "Register")

            #no data
            resp = self.client.post(reverse('auth.signup_form_normal'), follow=True)
            self.assertContains(resp, "Register")

            with patch("oneplus.auth_views.SearchQuerySet") as MockSearchSet:
                # non-empty search result
                MockSearchSet().filter().values.return_value = [{'pk': 1, 'name': 'Blargity School'}]
                resp = self.client.post(reverse('auth.signup_form_normal'),
                                        data={
                                            'first_name': "Bob",
                                            'surname': "Bobby",
                                            'cellphone': '0729876543',
                                            'province': 'Gauteng',
                                            'grade': 'Grade 10',
                                            'enrolled': 1,
                                            'school_dirty': 'blarg'},
                                        follow=True)
                MockSearchSet.assert_called()
                self.assertContains(resp, 'Blargity School')
                MockSearchSet.clear()

                # No search results
                MockSearchSet().filter().values.return_value = []
                resp = self.client.post(reverse('auth.signup_form_normal'),
                                        data={
                                            'first_name': "Bob",
                                            'surname': "Bobby",
                                            'cellphone': '0729876543',
                                            'province': 'Gauteng',
                                            'grade': 'Grade 10',
                                            'enrolled': 1,
                                            'school_dirty': 'blarg'},
                                        follow=True)
                MockSearchSet.assert_called()
                self.assertContains(resp, 'No schools were a close enough match')
                MockSearchSet.clear()

                # Failed ElasticSearch
                MockSearchSet().filter().values.side_effect = Exception('LOL! ERROR.')
                resp = self.client.post(reverse('auth.signup_form_normal'),
                                        data={
                                            'first_name': "Bob",
                                            'surname': "Bobby",
                                            'cellphone': '0729876543',
                                            'province': 'Gauteng',
                                            'grade': 'Grade 10',
                                            'enrolled': 1,
                                            'school_dirty': self.school.name},
                                        follow=True)
                MockSearchSet.assert_called()
                self.assertContains(resp, 'No schools were a close enough match')
                MockSearchSet.clear()

            #invalid school and class
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Bob",
                                        'surname': "Bobby",
                                        'cellphone': '0729876543',
                                        'province': 'Gauteng',
                                        'grade': 'Grade 10',
                                        'enrolled': 1,
                                        'school': 999
                                    },
                                    follow=True)
            self.assertContains(resp, "No such school exists")

            #valid data
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Bob",
                                        'surname': "Bobby",
                                        'cellphone': '0729876543',
                                        'province': 'Gauteng',
                                        'grade': 'Grade 10',
                                        'enrolled': 0,
                                        'school': promaths_school.id
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876543')
            self.assertEquals('Bob', new_learner.first_name)

            # valid - not enrolled - grade 10 - no open class created
            self.school.province = "Gauteng"
            self.school.save()
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Koos",
                                        'surname': "Botha",
                                        'cellphone': '0729876540',
                                        'grade': 'Grade 10',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876540')
            self.assertEquals('Koos', new_learner.first_name)

            try:
                School.objects.get(name=settings.OPEN_SCHOOL).delete()
            except School.DoesNotExist:
                pass

            # valid - not enrolled - grade 10
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Willy",
                                        'surname': "Wolly",
                                        'cellphone': '0729878963',
                                        'grade': 'Grade 10',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729878963')
            self.assertEquals('Willy', new_learner.first_name)

            self.course.name = settings.GRADE_11_COURSE_NAME
            self.course.save()

            # valid - not enrolled - grade 11 - creaing open class
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Tom",
                                        'surname': "Tom",
                                        'cellphone': '0729876576',
                                        'grade': 'Grade 11',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876576')
            self.assertEquals('Tom', new_learner.first_name)

            # valid - not enrolled - grade 11
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Henky",
                                        'surname': "Tanky",
                                        'cellphone': '0729876486',
                                        'grade': 'Grade 11',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876486')
            self.assertEquals('Henky', new_learner.first_name)

            resp = self.client.get(reverse("auth.signup_form_normal"))
            self.assertContains(resp, 'Let\'s sign you up')

            self.course.name = settings.GRADE_12_COURSE_NAME
            self.course.save()

            # valid - not enrolled - grade 12 - creaing open class
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Rob",
                                        'surname': "Web",
                                        'cellphone': '0729876599',
                                        'grade': 'Grade 12',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876599')
            self.assertEquals('Rob', new_learner.first_name)

            # valid - not enrolled - grade 12
            resp = self.client.post(reverse('auth.signup_school_confirm'),
                                    data={
                                        'first_name': "Kyle",
                                        'surname': "Evans",
                                        'cellphone': '0729876444',
                                        'grade': 'Grade 12',
                                        'province': "Gauteng",
                                        'school': self.school.id,
                                        'enrolled': 1,
                                    },
                                    follow=True)
            self.assertContains(resp, "Thank you")
            new_learner = Learner.objects.get(username='0729876444')
            self.assertEquals('Kyle', new_learner.first_name)

            resp = self.client.get(reverse("auth.signup_form_normal"))
            self.assertContains(resp, 'Let\'s sign you up')


class TestChangeDetails(TestCase):

    def setUp(self):

        self.organisation = Organisation.objects.get(name='One Plus')
        self.school = create_school('school name', self.organisation)
        self.learner = create_learner(
            self.school,
            username="+27123456789",
            mobile="+27123456789",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        self.course = create_course()
        self.module = create_module('module name', self.course)
        self.classs = create_class('class name', self.course)
        self.participant = create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))

        self.module = create_module('module name', self.course)
        self.badge_template = create_badgetemplate()

        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='1_CORRECT',
            course=self.course,
            module=self.module,
            badge=self.badge_template
        )
        self.outgoing_vumi_text = []
        self.outgoing_vumi_metrics = []
        self.handler = RecordingHandler()
        logger = logging.getLogger('DEBUG')
        logger.setLevel(logging.INFO)
        logger.addHandler(self.handler)

        self.admin_user_password = 'mypassword'
        self.admin_user = CustomUser.objects.create_superuser(
            username='asdf33',
            email='asdf33@example.com',
            password=self.admin_user_password,
            mobile='+27111111133')

    def test_change_details(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('auth.change_details'))
        self.assertEqual(resp.status_code, 200)

        # no change
        resp = self.client.post(reverse("auth.change_details"), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No changes made.")

        # invalid old_number
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '012'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please enter a valid mobile number.")

        # incorrect old_number
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27721234567'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This number is not associated with this account.")

        # invalid new_mobile
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27123456789',
                                      'new_number': '012'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please enter a valid mobile number.")

        # invalid new_mobile
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27123456789',
                                      'new_number': '+27123456789'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "You cannot change your number to your current number.")

        # new number same as an existing user
        learner = create_learner(
            self.school,
            username="+271234569999",
            mobile="+27123456999",
            email="abcd@abcd.com")

        self.participant = create_participant(
            learner,
            self.classs,
            datejoined=datetime.now())

        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27123456789',
                                      'new_number': '+27123456999'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A user with this mobile number (+27123456999) already exists.")

        self.learner.email = "qwer@qwer.com"
        self.learner.save()
        # incorrect old_email
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_email': 'xyz@xyz.com'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This email is not associated with this account.")

        # changing to current email
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_email': 'qwer@qwer.com',
                                      'new_email': 'qwer@qwer.com'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This is your current email.")

        # invalid new_email
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_email': 'qwer@qwer.com',
                                      'new_email': 'abc'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please enter a valid email.")

        # email exists
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_email': 'qwer@qwer.com',
                                      'new_email': 'abcd@abcd.com'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A user with this email (abcd@abcd.com) already exists.")

        # valid
        resp = self.client.post(reverse("auth.change_details"),
                                data={'old_number': '+27123456789',
                                      'new_number': '0721478529',
                                      'old_email': 'qwer@qwer.com',
                                      'new_email': 'asdf@asdf.com'},
                                follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Your number has been changed to 0721478529")
        self.assertContains(resp, "Your email has been changed to asdf@asdf.com.")

    def test_reset_password(self):
        new_learner = create_learner(
            self.school,
            username="0701234567",
            mobile="0701234567")

        new_participant = create_participant(
            new_learner,
            self.classs,
            datejoined=datetime.now())

        resp = self.client.get(reverse('auth.reset_password', kwargs={'token': 'abc'}), follow=True)
        self.assertRedirects(resp, '/onboarding')

        new_learner.pass_reset_token = "abc"
        new_learner.pass_reset_token_expiry = datetime.now() + timedelta(days=1)
        new_learner.save()

        resp = self.client.get(reverse('auth.reset_password', kwargs={'token': '%s' % new_learner.pass_reset_token}))
        self.assertEquals(resp.status_code, 200)

        #invalid form
        resp = self.client.post(reverse('auth.reset_password', kwargs={'token': '%s' % new_learner.pass_reset_token}),
                                data={})
        self.assertContains(resp, "Please enter your new password")

        #passwords not matching
        resp = self.client.post(reverse('auth.reset_password', kwargs={'token': '%s' % new_learner.pass_reset_token}),
                                data={
                                    "password": '123',
                                    "password_2": '23'
                                })
        self.assertContains(resp, "Passwords do not match")

        password = "12345"
        resp = self.client.post(reverse('auth.reset_password', kwargs={'token': '%s' % new_learner.pass_reset_token}),
                                data={
                                    "password": password,
                                    "password_2": password
                                })
        self.assertContains(resp, "Password changed")

        resp = self.client.post(
            reverse('auth.login'),
            data={
                'username': new_learner.username,
                'password': password},
            follow=True
        )
        self.assertContains(resp, "WELCOME")

    def test_login(self):
        resp = self.client.get(reverse('auth.login'))
        self.assertEquals(resp.status_code, 200)

        c = Client()

        resp = c.post(
            reverse('auth.login'),
            data={},
            follow=True
        )

        self.assertContains(resp, "Sign in")

        password = 'mypassword'
        my_admin = CustomUser.objects.create_superuser(
            username='asdf',
            email='asdf@example.com',
            password=password,
            mobile='+27111111111')

        c.login(username=my_admin.username, password=password)

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27198765432",
                'password': password},
            follow=True
        )

        self.assertContains(resp, "dig-it is currently in test phase")

        learner = Learner.objects.create_user(
            username="+27231231231",
            mobile="+27231231231",
            grade='Grade 11',
            password='1234'
        )
        learner.save()

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )

        self.assertContains(resp, "You are not currently linked to a class")

        learner.is_active = False
        learner.save()

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )
        self.assertContains(resp, "GET CONNECTED")

        learner.is_active = True
        learner.save()

        create_participant(learner, self.classs, datejoined=datetime.now())

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1235'},
            follow=True
        )

        self.assertContains(resp, "incorrect password")

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )

        self.assertContains(resp, "WELCOME")

        question1 = create_test_question('question1', self.module, question_content='test question')
        option1 = create_test_question_option(name="option1", question=question1, correct=True)

        LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.participant.answer(question1, option1)

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )

        self.assertContains(resp, "WELCOME")

        create_participant(learner, self.classs, datejoined=datetime.now())

        resp = c.post(
            reverse('auth.login'),
            data={
                'username': "+27231231231",
                'password': '1234'},
            follow=True
        )
        self.assertContains(resp, "Account Issue")
