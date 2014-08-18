from django.core.urlresolvers import reverse
from datetime import datetime, timedelta
from django.test import TestCase
from core.models import Participant, Class, Course, ParticipantQuestionAnswer
from organisation.models import Organisation, School, Module
from content.models import TestingBank, TestingQuestion, TestingQuestionOption
from gamification.models import GamificationScenario, GamificationPointBonus,\
    GamificationBadgeTemplate
from auth.models import Learner
from communication.models import Message, ChatGroup, ChatMessage
from oneplus.models import LearnerState
from templatetags.oneplus_extras import strip_tags, align, format_width
from mock import patch
from views import get_points_awarded, get_badge_awarded

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
        return School.objects.create(
            name=name, organisation=organisation, **kwargs)

    def create_learner(self, school, **kwargs):
        return Learner.objects.create(school=school, **kwargs)

    def create_participant(self, learner, classs, **kwargs):
        return Participant.objects.create(
            learner=learner, classs=classs, **kwargs)

    def create_testing_bank(self, name, module, **kwargs):
        return TestingBank.objects.create(name=name, module=module, **kwargs)

    def create_test_question(self, name, bank, **kwargs):
        return TestingQuestion.objects.create(name=name, bank=bank, **kwargs)

    def create_test_question_option(self, name, bank, **kwargs):
        return TestingQuestion.objects.create(name=name, bank=bank, **kwargs)

    def create_badgetemplate(self, name='badge template name', **kwargs):
        return GamificationBadgeTemplate.objects.create(name=name, **kwargs)

    def create_pointbonus(self, name='point bonus name', **kwargs):
        return GamificationPointBonus.objects.create(name=name, **kwargs)

    def create_message(self, author, course, **kwargs):
        return Message.objects.create(author=author, course=course, **kwargs)

    def create_test_question_option(self, name, question):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=True)

    def create_test_answer(
            self,
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

    def create_and_answer_questions(self, num_questions, prefix, date):
        answers = []
        for x in range(0, num_questions):
            # Create a question
            question = self.create_test_question('q' + prefix + str(x),
                                                 self.testbank)
            question.save()
            option = self.create_test_question_option(
                'option_' + prefix + str(x),
                question)
            option.save()
            answer = self.create_test_answer(
                participant=self.participant,
                question=question,
                option_selected=option,
                answerdate=date
            )
            answer.save()
            answers.append(answer)

        return answers

    def setUp(self):
        self.course = self.create_course()
        self.classs = self.create_class('class name', self.course)
        self.organisation = self.create_organisation()
        self.school = self.create_school('school name', self.organisation)
        self.learner = self.create_learner(
            self.school,
            username="+27123456789",
            country="country",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30))
        self.participant = self.create_participant(
            self.learner, self.classs, datejoined=datetime.now())
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
        self.create_test_question('question1', self.testbank)
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=None,
        )

        # get next question
        learnerstate.getnextquestion()
        learnerstate.save()

        # check active question
        self.assertEquals(learnerstate.active_question.name, 'question1')

    def test_home(self):
        self.create_test_question('question1', self.testbank)
        LearnerState.objects.create(
            participant=self.participant,
            active_question=None,
        )
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        resp = self.client.get(reverse('learn.home'))
        self.assertEquals(resp.status_code, 200)

    def test_nextchallenge(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        question1 = self.create_test_question(
            'question1', self.testbank, question_content='test question')
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

        resp = self.client.post(
            reverse('learn.next'),
            data={'answer': questionoption1.id})

    def test_rightanswer(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )
        question1 = self.create_test_question(
            'question1',
            self.testbank,
            question_content='test question')
        LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        resp = self.client.get(reverse('learn.right'))
        self.assertEquals(resp.status_code, 200)

    def test_wronganswer(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token}))
        question1 = self.create_test_question(
            'question1',
            self.testbank,
            question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=False,
        )
        resp = self.client.get(reverse('learn.wrong'))
        self.assertEquals(resp.status_code, 200)

    def test_inbox(self):
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )
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
        self.client.get(
            reverse(
                'auth.autologin',
                kwargs={'token': self.learner.unique_token})
        )
        msg = self.create_message(
            self.learner,
            self.course, name="msg",
            publishdate=datetime.now(),
            content='test message'
        )

        resp = self.client.get(
            reverse('com.inbox_detail', kwargs={'messageid': msg.id}))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'test message')

    def test_chat(self):
        self.client.get(reverse('auth.autologin',
                                kwargs={'token': self.learner.unique_token}))
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

        resp = self.client.get(reverse(
            'com.chat',
            kwargs={'chatid': chatgroup.id})
        )
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, 'chatmsg1content')

    @patch.object(LearnerState, 'today')
    def test_training_sunday(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 20, 1, 1, 1)

        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_training_saturday(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 19, 1, 1, 1)

        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')

        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )

        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_monday_first_week_no_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 21, 1, 1, 1)

        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_monday_first_week_with_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 21, 1, 1, 1)

        self.create_and_answer_questions(
            3,
            'sunday',
            datetime(2014, 7, 20, 1, 1, 1))

        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 0)

    @patch.object(LearnerState, 'today')
    def test_tuesday_with_monday(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 22, 1, 1, 1)

        self.create_and_answer_questions(
            3,
            'sunday',
            datetime(2014, 7, 21, 1, 1, 1))

        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_miss_a_day_during_week(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 22, 1, 1, 1)
        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 6)

    @patch.object(LearnerState, 'today')
    def test_miss_multiple_days_during_week(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 23, 1, 1, 1)
        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 9)

    @patch.object(LearnerState, 'today')
    def test_partially_miss_day_during_week(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 22, 1, 1, 1)
        self.create_and_answer_questions(
            2,
            'sunday',
            datetime(2014, 7, 21, 1, 1, 1))

        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 4)

    @patch.object(LearnerState, 'today')
    def test_forget_a_single_days_till_weekend(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 26, 1, 1, 1)

        self.create_and_answer_questions(3, 'monday',
                                         datetime(2014, 7, 21, 1, 1, 1))
        self.create_and_answer_questions(3, 'tuesday',
                                         datetime(2014, 7, 22, 1, 1, 1))
        self.create_and_answer_questions(3, 'wednesday',
                                         datetime(2014, 7, 23, 1, 1, 1))
        self.create_and_answer_questions(3, 'thursday',
                                         datetime(2014, 7, 24, 1, 1, 1))

        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    @patch.object(LearnerState, 'today')
    def test_miss_all_days_till_weekend_except_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 26, 1, 1, 1)

        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        self.create_and_answer_questions(3, 'training',
                                         datetime(2014, 7, 20, 1, 1, 1))
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 12)

    @patch.object(LearnerState, 'today')
    def test_miss_all_questions_except_training(self, mock_get_today):
        mock_get_today.return_value = datetime(2014, 7, 28, 1, 1, 1)

        question1 = self.create_test_question('question1', self.testbank,
                                              question_content='test question')
        self.create_and_answer_questions(3, 'training',
                                         datetime(2014, 7, 20, 1, 1, 1))
        learnerstate = LearnerState.objects.create(
            participant=self.participant,
            active_question=question1,
            active_result=True,
        )
        self.assertEquals(learnerstate.get_total_questions(), 3)

    def test_strip_tags(self):
        content = "<p><b>Test</b></p>"
        result = strip_tags(content)
        self.assertEquals(result, "<b>Test</b>")

    def test_align_image_only(self):
        content = "<img/>"
        result = align(content)
        self.assertEquals(result, u'<div style="vertical-align:middle;'
                                  u'display:inline-block;width:80%">'
                                  u'<img style="vertical-align:middle"/>'
                                  u'</div>')

    def test_align_text_only(self):
        content = "Test"
        result = align(content)
        self.assertEquals(result, u'<div style="vertical-align:middle;'
                                  u'display:inline-block;width:80%">'
                                  u'Test</div>')

    def test_align_text_and_image(self):
        content = "<b>Test</b><img/>"
        result = align(content)
        self.assertEquals(result, u'<div style="vertical-align:middle;'
                                  u'display:inline-block;width:80%">'
                                  u'<b>Test</b><img style='
                                  u'"vertical-align:middle"/></div>')

    def test_align_double_image(self):
        content = "<img/><img/>"
        result = align(content)
        self.assertEquals(result, u'<div style="vertical-align:middle;'
                                  u'display:inline-block;width:80%">'
                                  u'<img style="vertical-align:middle"/>'
                                  u'<img style="vertical-align:middle"/>'
                                  u'</div>')

    def test_align_then_strip(self):
        content = "<b>Test</b><p></p><img/>"
        result = align(content)
        output = strip_tags(result)
        self.assertEquals(output, u'<div style="vertical-align:middle;'
                                  u'display:inline-block;width:80%">'
                                  u'<b>Test</b><img style="'
                                  u'vertical-align:middle"/></div>')

    def test_format_width(self):
        content = '<img style="width:300px"/>'
        result = format_width(content)
        self.assertEquals(result, u'<body><img style="width:100%"/></body>')

    def test_filters_empty(self):
        content = ""
        result = align(content)
        output = strip_tags(result)
        self.assertEquals(output, u'<div></div>')
        

    def test_right_view(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        question = self.create_test_question('question1', self.testbank,
                                             question_content='test question')
        questionoption = self.create_test_question_option('questionoption1',
                                                          question)

        # Post a correct answer
        self.client.post(
            reverse('learn.next'),
            data={'answer': questionoption.id}
        )
        point = get_points_awarded(self.participant)
        badge, badge_points = get_badge_awarded(self.participant)
        self.assertEqual(point, 5)
        self.assertEqual(badge, self.badge_template)

    def test_right_view_(self):
        self.client.get(reverse(
            'auth.autologin',
            kwargs={'token': self.learner.unique_token})
        )
        question = self.create_test_question('question1', self.testbank,
                                             question_content='test question')
        questionoption = self.create_test_question_option('questionoption1',
                                                          question)

        # Post a correct answer
        self.client.post(
            reverse('learn.next'),
            data={'answer': questionoption.id}
        )
        point = get_points_awarded(self.participant)
        badge, badge_points = get_badge_awarded(self.participant)
        self.assertEqual(point, 5)
        self.assertEqual(badge, self.badge_template)

