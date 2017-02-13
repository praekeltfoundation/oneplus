# -*- coding: utf-8 -*-
from communication.models import Post, CoursePostRel
from datetime import datetime, timedelta
from auth.models import Learner
from content.models import TestingQuestion, TestingQuestionOption
from core.models import Participant, ParticipantQuestionAnswer, Class, ParticipantRedoQuestionAnswer
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from organisation.models import Module, CourseModuleRel, School, Course, Organisation
from oneplus.models import LearnerState


def create_test_question(name, module, **kwargs):
        return TestingQuestion.objects.create(name=name, module=module, **kwargs)


def create_learner(school, **kwargs):
    if 'grade' not in kwargs:
        kwargs['grade'] = 'Grade 11'
    return Learner.objects.create(school=school, **kwargs)


def create_module(name, course, **kwargs):
    module = Module.objects.create(name=name, **kwargs)
    rel = CourseModuleRel.objects.create(course=course, module=module)
    module.save()
    rel.save()
    return module


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


def create_organisation(name='organisation name', **kwargs):
    return Organisation.objects.create(name=name, **kwargs)


def create_class(name, course, **kwargs):
    return Class.objects.create(name=name, course=course, **kwargs)


@override_settings(VUMI_GO_FAKE=True)
class TestCommentsOnLatestBlog(TestCase):
    def setUp(self):

        self.organisation = Organisation.objects.get(name='One Plus')
        self.school = create_school('Death Dome', self.organisation)
        self.learner = create_learner(
            self.school,
            username="+27123456789",
            mobile="+27123456789",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        self.course = create_course('Hunger Games')
        self.classs = create_class('District 12', self.course)
        self.participant = create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))

    def test_blog(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        #Creating the first blog post and commenting should be allowed to happen
        blog_first_created = Post.objects.create(name='Round1', publishdate=datetime.now() - timedelta(days=1))
        CoursePostRel.objects.create(course=self.course, post=blog_first_created)

        resp = self.client.get(reverse('com.blog', kwargs={'blogid': blog_first_created.id}), follow=True)
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('com.blog', kwargs={'blogid': blog_first_created.id}), data={'comment': 'CookiePant'}, follow=True)

        self.assertEquals(resp.status_code, 200)
        message = "message will display"
        self.assertContains(resp, message)

        #Create second blog now this is the latest and commenting should only be allowed here and not on the first blog
        blog_second_created = Post.objects.create(name='Round2', publishdate=datetime.now())
        CoursePostRel.objects.create(course=self.course, post=blog_second_created)

        resp = self.client.get(reverse('com.blog', kwargs={'blogid': blog_second_created.id}))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('com.blog', kwargs={'blogid': blog_second_created.id}), data={'comment': 'Tuna Cake'}, follow=True)

        self.assertEquals(resp.status_code, 200)
        message = "message will display"
        self.assertContains(resp, message)

        resp = self.client.get(reverse('com.blog', kwargs={'blogid': blog_first_created.id}))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Comment", count=0)


@override_settings(VUMI_GO_FAKE=True)
class TestFlashMessage(TestCase):
    def setUp(self):
        self.course = create_course()
        self.classs = create_class('Slytherin', self.course)
        self.organisation = create_organisation()
        self.school = create_school('Hogwarts', self.organisation)
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

    def test_discuss_flash_message(self):
        # User logs in to test commenting
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))

        self.test_question = create_test_question("question1", self.module, state=TestingQuestion.PUBLISHED)
        self.question_option_right = create_test_question_option("question1_right",
                                                                 self.test_question,
                                                                 correct=True)

        self.question_option_wrong = create_test_question_option("question1_wrong",
                                                                 self.test_question,
                                                                 correct=False)

        self.client.get(reverse("learn.next"))
        self.client.post(reverse("learn.next"), data={"answer": self.question_option_right.id}, follow=True)
        self.client.get(reverse("learn.right"))
        message = 'Sssssayiacchhhassiiiyyyeeth'
        empty_message = ''
        #Test 1.1: correct data given to show right.html
        resp = self.client.post(reverse('learn.right'),
                                data={'comment': message},
                                follow=True)
        self.assertContains(resp, "<p>%s</p>" % (message,), html=True)

        #Test 1.2: correct data given to show right.html with empty message
        resp = self.client.post(reverse('learn.right'),
                                data={'comment': empty_message},
                                follow=True)
        self.assertEquals(resp.status_code, 200)

        ParticipantQuestionAnswer.objects.all().delete()
        LearnerState.objects.all().delete()
        self.client.get(reverse("learn.next"))
        self.client.post(reverse("learn.next"), data={"answer": self.question_option_wrong.id}, follow=True)
        self.client.get(reverse("learn.wrong"))

        #Test 2.1: incorrect data given to show wrong.html
        message = 'He is just a puppy'
        resp = self.client.post(reverse('learn.wrong'),
                                data={'comment': message},
                                follow=True)
        self.assertContains(resp, message)

        #Test 2.2: incorrect data given to show wrong.html with empty message
        self.client.post(reverse('learn.wrong'),
                         data={'comment': empty_message},
                         follow=True)
        self.assertEquals(resp.status_code, 200)

        self.client.get(reverse("learn.redo"))
        self.client.post(reverse("learn.redo"), data={"answer": self.question_option_right.id}, follow=True)
        self.client.get(reverse("learn.redo_right"))

        #Test 3.1: correct data given in redo to show redo_right.html
        message = 'My Father will hear about this'
        resp = self.client.post(reverse('learn.redo_right'),
                                data={'comment': message},
                                follow=True)
        self.assertContains(resp, message)

        #Test 3.2: correct data given in redo to show redo_right.html with empty message
        resp = self.client.post(reverse('learn.redo_right'),
                                data={'comment': empty_message},
                                follow=True)
        self.assertEquals(resp.status_code, 200)

        ParticipantRedoQuestionAnswer.objects.all().delete()
        self.client.get(reverse("learn.redo"))
        self.client.post(reverse("learn.redo"), data={"answer": self.question_option_wrong.id}, follow=True)
        self.client.get(reverse("learn.redo_wrong"))

        #Test 4.1: incorrect data given in redo to show redo_wrong.html
        message = 'The boy who lived, come to die'
        resp = self.client.post(reverse('learn.redo_wrong'),
                                data={'comment': message},
                                follow=True)
        self.assertContains(resp, "<p>%s</p>" % (message,), html=True)

        #Test 4.2: incorrect data given in redo to show redo_wrong.html with empty message
        resp = self.client.post(reverse('learn.redo_wrong'),
                                data={'comment': empty_message},
                                follow=True)
        self.assertEquals(resp.status_code, 200)
