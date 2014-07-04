from django.core.urlresolvers import reverse

from datetime import datetime, timedelta


from django.test import TestCase
from models import LearnerState
from core.models import Participant, Class, Course
from organisation.models import Organisation, School, Module
from content.models import TestingBank, TestingQuestion, TestingQuestionOption
from gamification.models import GamificationScenario, GamificationPointBonus, GamificationBadgeTemplate
from auth.models import Learner, CustomUser
from communication.models import Message, ChatGroup, ChatMessage


class GeneralTests(TestCase):

    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_module(self, name, course, **kwargs):
        return Module.objects.create(name=name, course=course, **kwargs)

    def create_class(self, name, course, **kwargs):
        return Class.objects.create(name=name, course=course, **kwargs)

    def create_organisation(self, name='organisation name', **kwargs):
        return Organisation.objects.create(name=name, **kwargs)

    def create_school(self, name, organisation, **kwargs):
        return School.objects.create(name=name, organisation=organisation, **kwargs)

    def create_learner(self, school, **kwargs):
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        return Participant.objects.create(learner=learner, classs=classs, **kwargs)

    def create_testing_bank(self, name, module, **kwargs):
        return TestingBank.objects.create(name=name, module=module, **kwargs)

    def create_test_question(self, name, bank, **kwargs):
        return TestingQuestion.objects.create(name=name, bank=bank, **kwargs)

    def create_badgetemplate(self, name='badge template name', **kwargs):
        return GamificationBadgeTemplate.objects.create(name=name, **kwargs)

    def create_pointbonus(self, name='point bonus name', **kwargs):
        return GamificationPointBonus.objects.create(name=name, **kwargs)

    def create_message(self, author, course, **kwargs):
        return Message.objects.create(author=author, course=course, **kwargs)

    def setUp(self):
        self.course = self.create_course()
        self.classs = self.create_class('class name', self.course)
        self.organisation = self.create_organisation()
        self.school = self.create_school('school name', self.organisation)
        self.learner = self.create_learner(self.school,
                                           username="+27123456789",
                                           country="country",
                                           unique_token='abc123',
                                           unique_token_expiry=datetime.now() + timedelta(days=30))
        self.participant = self.create_participant(self.learner, self.classs, datejoined=datetime.now())
        self.module = self.create_module('module name', self.course)
        self.testbank = self.create_testing_bank('testbank name', self.module)
        self.badge_template = self.create_badgetemplate()

        self.pointbonus = self.create_pointbonus(value=5)
        self.scenario = GamificationScenario.objects.create(
            name='scenario name',
            event='CORRECT',
            course=self.course,
            module=self.module,
            point=self.pointbonus,
            badge=self.badge_template
        )

    def test_get_next_question(self):
        question1 = self.create_test_question('question1', self.testbank)
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=None,
        )

        #get next question
        learnerstate.getnextquestion()
        learnerstate.save()

        #check active question
        self.assertEquals(learnerstate.active_question.name, 'question1')

    def test_home(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        resp = self.client.get(reverse('learn.home'))
        self.assertEquals(resp.status_code, 200)

    def test_nextchallenge(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        question1 = self.create_test_question('question1', self.testbank, question_content='test question')
        questionoption1 = TestingQuestionOption.objects.create(
            name='questionoption1',
            question=question1,
            content='questionanswer1',
            correct=True
        )

        resp = self.client.get(reverse('learn.next'))
        self.assertEquals(resp.status_code, 200)

        self.assertContains(resp, 'test question')
        self.assertContains(resp, 'questionanswer1')

        resp = self.client.post(reverse('learn.next'), data={'answer': questionoption1.id})

    def test_rightanswer(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        question1 = self.create_test_question('question1', self.testbank, question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        resp = self.client.get(reverse('learn.right'))
        self.assertEquals(resp.status_code, 200)

    def test_wronganswer(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        question1 = self.create_test_question('question1', self.testbank, question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=False,
        )
        resp = self.client.get(reverse('learn.wrong'))
        self.assertEquals(resp.status_code, 200)

    def test_inbox(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        msg = self.create_message(
            self.learner,
            self.course, name="msg",
            publishdate=datetime.now(),
            content='test message'
        )

        resp = self.client.get(reverse('com.inbox'))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'test message')

    def test_inbox_detail(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        msg = self.create_message(
            self.learner,
            self.course, name="msg",
            publishdate=datetime.now(),
            content='test message'
        )

        resp = self.client.get(reverse('com.inbox_detail', kwargs={'messageid': msg.id}))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'test message')

    def test_chat(self):
        self.client.get(reverse('auth.autologin', kwargs={'token': self.learner.unique_token}))
        chatgroup = ChatGroup.objects.create(
            name='testchatgroup',
            course=self.course
        )
        chatmsg1 = ChatMessage.objects.create(
            chatgroup=chatgroup,
            author=self.learner,
            content='chatmsg1content',
            publishdate=datetime.now()
        )

        resp = self.client.get(reverse('com.chat', kwargs={'chatid': chatgroup.id}))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'chatmsg1content')




