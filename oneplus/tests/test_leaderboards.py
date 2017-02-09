# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from auth.models import Learner
from content.models import TestingQuestion, TestingQuestionOption
from django.test import TestCase
from django.core.urlresolvers import reverse
from organisation.models import Module, CourseModuleRel, School, Course, Organisation
from django.utils import timezone
from core.models import Class, Participant, ParticipantQuestionAnswer


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


class TestLeaderboards(TestCase):

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

    def test_leaderboard_screen(self):
        question_list = list()
        question_option_list = list()
        question_option_wrong_list = list()

        for x in range(0, 11):
            question = create_test_question('question_%s' % x,
                                            self.module,
                                            question_content='test question',
                                            state=3)
            question_option = create_test_question_option('question_option_%s' % x, question)
            question_wrong_option = create_test_question_option('question_option_w_%s' % x, question, False)

            question_list.append(question)
            question_option_list.append(question_option)
            question_option_wrong_list.append(question_wrong_option)

        all_learners_classes = []
        all_particpants_classes = []
        all_learners = []
        all_particpants = []
        counter = 0
        password = "12345"

        test_class = create_class('test_class', self.course)

        for x in range(10, 21):
            all_learners.append(create_learner(self.school,
                                               first_name="test_%s" % x,
                                               username="07612345%s" % x,
                                               mobile="07612345%s" % x,
                                               unique_token='%s' % x,
                                               unique_token_expiry=datetime.now() + timedelta(days=30)))
            all_learners[counter].set_password(password)

            all_particpants.append(
                create_participant(all_learners[counter], test_class, datejoined=datetime.now()))

            for y in range(0, counter+1):
                all_particpants[y].answer(question_list[y], question_option_list[y])
                all_particpants[y].answer(question_list[y], question_option_list[y])

            #data for class leaderboard
            new_class = create_class('class_%s' % x, self.course)
            all_learners_classes.append(create_learner(self.school,
                                                       first_name="test_b_%s" % x,
                                                       username="08612345%s" % x,
                                                       mobile="08612345%s" % x,
                                                       unique_token='abc%s' % x,
                                                       unique_token_expiry=datetime.now() + timedelta(days=30)))
            all_learners_classes[counter].set_password(password)

            all_particpants_classes.append(create_participant(all_learners_classes[counter],
                                                              new_class, datejoined=datetime.now()))

            for y in range(0, counter+1):
                all_particpants_classes[y].answer(question_list[y], question_option_wrong_list[y])

            all_particpants_classes[counter].answer(question_list[counter], question_option_list[counter])
            all_particpants_classes[counter].answer(question_list[counter], question_option_list[counter])
            all_particpants_classes[counter].answer(question_list[counter], question_option_wrong_list[counter])
            all_particpants_classes[counter].answer(question_list[counter], question_option_wrong_list[counter])

            counter += 1

        self.client.get(
            reverse('auth.autologin', kwargs={'token': "20"}))

        resp = self.client.get(reverse('prog.leader'))
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(reverse('prog.leader'), follow=True)
        self.assertEquals(resp.status_code, 200)

        # overall leaderboard is overall in class, not over all classes
        resp = self.client.get(reverse('prog.leader'), follow=True)

        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_20")
        self.assertContains(resp, "11th place")
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")
        self.assertContains(resp, "Show more", count=3)

        self.client.get(
            reverse('auth.autologin', kwargs={'token': "14"}))

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "test_14")
        self.assertContains(resp, "5<sup>th</sup> place")
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")
        self.assertContains(resp, "Show more", count=3)

    def test_leaderboard_collapse(self):
        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")
        self.assertContains(resp, "Show more", count=3)

        resp = self.client.post(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")
        self.assertContains(resp, "Show more", count=3)

        resp = self.client.post(reverse('prog.leader'), data={'board.class.active': 'true'}, follow=True)
        self.assertContains(resp, "Show more", count=2)
        self.assertContains(resp, "Show less", count=1)

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Show more", count=2)
        self.assertContains(resp, "Show less", count=1)

        resp = self.client.post(reverse('prog.leader'),
                                data={
                                    'board.class.active': 'true',
                                    'board.school.active': 'true',
                                    'board.national.active': 'true'},
                                follow=True)
        self.assertContains(resp, "Show more", count=0)
        self.assertContains(resp, "Show less", count=3)

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Show more", count=0)
        self.assertContains(resp, "Show less", count=3)

        resp = self.client.post(reverse('prog.leader'),
                                data={
                                    'board.class.active': 'false',
                                    'board.school.active': 'false',
                                    'board.national.active': 'false'},
                                follow=True)
        self.assertContains(resp, "Show more", count=3)
        self.assertContains(resp, "Show less", count=0)

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertContains(resp, "Show more", count=3)
        self.assertContains(resp, "Show less", count=0)

    def test_leaderboard_with_almost_no_results(self):
        self.client.get(
            reverse('auth.autologin',
                    kwargs={'token': self.learner.unique_token})
        )

        resp = self.client.get(reverse('prog.leader'), follow=True)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "1<sup>st</sup> place", count=3)
        self.assertContains(resp, "Grade Leaderboard")
        self.assertContains(resp, "School Leaderboard")
        self.assertContains(resp, "National Leaderboard")

    def test_leaderboard_school_multiple_entrants(self):
        school = create_school('Some Random School', self.organisation)
        learner1 = create_learner(school,
                                  first_name="learner_1",
                                  grade="Grade 11",
                                  mobile="1111111111",
                                  unique_token='blargity',
                                  unique_token_expiry=datetime.now() + timedelta(days=30),
                                  username="1111111111")

        learner2 = create_learner(school,
                                  first_name="learner_2",
                                  grade="Grade 11",
                                  mobile="2222222222",
                                  username="2222222222")

        learner3 = create_learner(school,
                                  first_name="learner_3",
                                  grade="Grade 11",
                                  mobile="3333333333",
                                  username="3333333333")

        participant1 = create_participant(learner1,
                                          self.classs,
                                          datejoined=timezone.now(),
                                          is_active=True,
                                          points=5)

        participant2 = create_participant(learner2,
                                          self.classs,
                                          datejoined=timezone.now(),
                                          is_active=True,
                                          points=10)

        participant3 = create_participant(learner3,
                                          self.classs,
                                          datejoined=timezone.now(),
                                          is_active=True,
                                          points=15)

        self.school.name = 'First School'
        self.school.save()
        self.learner.grade = 'Grade 11'
        self.learner.save()
        self.participant.points = 1
        self.participant.save()

        self.client.get(
            reverse('auth.autologin', kwargs={'token': learner1.unique_token})
        )
        resp = self.client.post(reverse('prog.leader'), data={'board.school.active': 'true'}, follow=True)

        self.assertContains(resp, school.name, count=1)
        self.assertContains(resp, self.school.name, count=1)
