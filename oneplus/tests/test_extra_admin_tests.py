from datetime import datetime, timedelta
import logging
from auth.models import Learner, CustomUser
from communication.models import Message, Post, PostComment, ChatGroup, ChatMessage, Report, ReportResponse, Sms, \
    SmsQueue, Discussion, CoursePostRel
from content.models import TestingQuestion, TestingQuestionOption
from core.models import Class, Participant, ParticipantQuestionAnswer, ParticipantBadgeTemplateRel
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from gamification.models import GamificationBadgeTemplate, GamificationPointBonus, GamificationScenario
from go_http.tests.test_send import RecordingHandler
from organisation.models import Course, Module, CourseModuleRel, Organisation, School


class ExtraAdminBitTests(TestCase):
    def create_course(self, name="course name", **kwargs):
        return Course.objects.create(name=name, **kwargs)

    def create_module(self, name, course, **kwargs):
        module = Module.objects.create(name=name, **kwargs)
        rel = CourseModuleRel.objects.create(course=course, module=module)
        module.save()
        rel.save()
        return module

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
        participant = Participant.objects.create(
            learner=learner, classs=classs, **kwargs)

        return participant

    def create_test_question(self, name, module, **kwargs):
        return TestingQuestion.objects.create(name=name,
                                              module=module,
                                              **kwargs)

    def create_badgetemplate(self, name='badge template name', **kwargs):
        return GamificationBadgeTemplate.objects.create(
            name=name,
            image="none",
            **kwargs)

    def create_gamification_point_bonus(self, name, value, **kwargs):
        return GamificationPointBonus.objects.create(
            name=name,
            value=value,
            **kwargs)

    def create_gamification_scenario(self, **kwargs):
        return GamificationScenario.objects.create(**kwargs)

    def create_message(self, author, course, **kwargs):
        return Message.objects.create(author=author, course=course, **kwargs)

    def create_post(self, name="Test Post", description="Test", content="Test content"):
        post = Post.objects.create(
            name=name,
            description=description,
            content=content,
            publishdate=datetime.now(),
            moderated=True
        )
        CoursePostRel.objects.create(course=self.course, post=post)

        return post

    def create_post_comment(self, post, author, content="Test Content"):
        return PostComment.objects.create(
            author=author,
            post=post,
            content=content,
            publishdate=datetime.now()
        )

    def create_chat_group(self, course, name="Test Chat Group", description="Test"):
        return ChatGroup.objects.create(
            name=name,
            description=description,
            course=course
        )

    def create_chat_message(self, chat_group, author, content="Test"):
        return ChatMessage.objects.create(
            chatgroup=chat_group,
            author=author,
            content=content,
            publishdate=datetime.now()
        )

    def create_and_answer_questions(self, num_questions, prefix, date, correct=False):
        answers = []
        for x in range(0, num_questions):
            # Create a question
            question = self.create_test_question(
                'q' + prefix + str(x), self.module)

            question.save()
            option = self.create_test_question_option(
                'option_' + prefix + str(x),
                question)
            option.save()
            answer = self.create_test_answer(
                participant=self.participant,
                question=question,
                option_selected=option,
                answerdate=date,
                correct=correct
            )
            answer.save()
            answers.append(answer)

        return answers

    def create_test_question_option(self, name, question, correct=True):
        return TestingQuestionOption.objects.create(
            name=name, question=question, correct=correct)

    def create_test_answer(
            self,
            participant,
            question,
            option_selected,
            answerdate,
            correct):
        return ParticipantQuestionAnswer.objects.create(
            participant=participant,
            question=question,
            option_selected=option_selected,
            answerdate=answerdate,
            correct=correct
        )

    def setUp(self):
        self.course = self.create_course()
        self.classs = self.create_class('class name', self.course)
        self.organisation = self.create_organisation()
        self.school = self.create_school('school name', self.organisation)
        self.learner = self.create_learner(
            self.school,
            username="+27123456789",
            mobile="+27123456789",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True)
        self.participant = self.create_participant(
            self.learner, self.classs, datejoined=datetime(2014, 7, 18, 1, 1))
        self.module = self.create_module('module name', self.course)
        self.badge_template = self.create_badgetemplate()

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

        self.chat_group = self.create_chat_group(self.course)

    def test_admin_report_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.question = self.create_test_question('q1', self.module)

        resp = c.get('/report_response/1000')
        self.assertContains(resp, 'Report 1000 not found')

        learner = self.create_learner(
            self.school,
            username="+27123456780",
            mobile="+27123456780",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        rep = Report.objects.create(
            user=learner,
            question=self.question,
            issue='e != mc^2',
            fix='e == 42',
            publish_date=datetime.now()
        )

        resp = c.get('/report_response/%s' % rep.id)
        self.assertContains(resp, 'Participant not found')

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 1, 18, 1, 1)
        )

        resp = c.get('/report_response/%s' % rep.id)
        self.assertContains(resp, 'Report Response')

        resp = c.post('/report_response/%s' % rep.id,
                      data={
                          'title': '',
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/report_response/%s' % rep.id,
                      data={
                          'title': '',
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('/report_response/%s' % rep.id)
        self.assertContains(resp, 'This field is required.')

        rr_cnt = ReportResponse.objects.all().count()
        msg_cnt = Message.objects.all().count()

        resp = c.post('/report_response/%s' % rep.id,
                      data={
                          'title': 'test',
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        self.assertEquals(ReportResponse.objects.all().count(), rr_cnt + 1)
        self.assertEquals(Message.objects.all().count(), msg_cnt + 1)

        resp = c.get('/report_response/%s' % rep.id)
        self.assertContains(resp, 'Report Response')

    def test_admin_msg_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        question = self.create_test_question('q5', self.module)

        resp = c.get('/message_response/1000')
        self.assertContains(resp, 'Message 1000 not found')

        learner = self.create_learner(
            self.school,
            username="+27223456780",
            mobile="+27223456780",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        msg = self.create_message(
            learner,
            self.course, name="msg",
            publishdate=datetime.now(),
            content='test message'
        )

        resp = c.get('/message_response/%s' % msg.id)
        self.assertContains(resp, 'Participant not found')

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 3, 18, 1, 1)
        )

        resp = c.get('/message_response/%s' % msg.id)
        self.assertContains(resp, 'Respond to Message')

        resp = c.post('/message_response/%s' % msg.id,
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/message_response/%s' % msg.id,
                      data={
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('/message_response/%s' % msg.id)
        self.assertContains(resp, 'This field is required.')

        msg_cnt = Message.objects.all().count()

        resp = c.post('/message_response/%s' % msg.id,
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        self.assertEquals(Message.objects.all().count(), msg_cnt + 1)
        msg = Message.objects.get(pk=msg.id)
        self.assertEquals(msg.responded, True)
        self.assertEquals(msg.responddate.date(), datetime.now().date())

    def test_admin_sms_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        resp = c.get('/sms_response/1000')
        self.assertContains(resp, 'Sms 1000 not found')

        learner = self.create_learner(
            self.school,
            username="+27223456781",
            mobile="+27223456781",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        sms = Sms.objects.create(
            uuid='123123123',
            message='test',
            msisdn=learner.mobile,
            date_sent=datetime.now()
        )

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 3, 18, 1, 1)
        )

        resp = c.get('/sms_response/%s' % sms.id)
        self.assertContains(resp, 'Respond to SMS')

        resp = c.post('/sms_response/%s' % sms.id,
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/sms_response/%s' % sms.id,
                      data={
                          'title': '',
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('/sms_response/%s' % sms.id)
        self.assertContains(resp, 'This field is required.')

        resp = c.post('/sms_response/%s' % sms.id,
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': 'Test24'
                      })

        sms = Sms.objects.get(pk=sms.id)
        self.assertEquals(sms.responded, True)
        self.assertEquals(sms.respond_date.date(), datetime.now().date())
        self.assertIsNotNone(sms.response)

        qsms = SmsQueue.objects.get(msisdn=learner.mobile)
        self.assertEquals(qsms.message, 'Test24')

        resp = c.get('/sms_response/%s' % sms.id)
        self.assertContains(resp, 'Respond to SMS')

    def test_admin_discussion_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        burl = '/discussion_response/'

        question = self.create_test_question('q7', self.module)

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'Discussion 1000 not found')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456788",
            mobile="+27223456788",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        disc = Discussion.objects.create(
            name='Test',
            description='Test',
            content='Test content',
            author=learner,
            publishdate=datetime.now(),
            course=self.course,
            module=self.module,
            question=question
        )

        resp = c.get('%s%s' % (burl, disc.id))
        self.assertContains(resp, 'Participant not found')

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 3, 18, 1, 1)
        )

        resp = c.get('%s%s' % (burl, disc.id))
        self.assertContains(resp, 'Respond to Discussion')

        resp = c.post('%s%s' % (burl, disc.id),
                      data={
                          'title': '',
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, disc.id),
                      data={
                          'title': '',
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s' % (burl, disc.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, disc.id),
                      data={
                          'title': 'test',
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        disc = Discussion.objects.get(pk=disc.id)
        self.assertIsNotNone(disc.response)
        self.assertEquals(disc.response.moderated, True)
        self.assertEquals(disc.response.author, self.admin_user)

        resp = c.get('%s%s' % (burl, disc.id))
        self.assertContains(resp, 'Respond to Discussion')

    def test_admin_discussion_response_selected(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        burl = '/discussion_response_selected/'

        question = self.create_test_question('q9', self.module)

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'All the selected Discussions have been responded too')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456888",
            mobile="+27223456888",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        disc = Discussion.objects.create(
            name='Test',
            description='Test',
            content='Test content',
            author=learner,
            publishdate=datetime.now(),
            course=self.course,
            module=self.module,
            question=question
        )

        disc2 = Discussion.objects.create(
            name='Test',
            description='Test',
            content='Test content again',
            author=learner,
            publishdate=datetime.now(),
            course=self.course,
            module=self.module,
            question=question
        )

        participant = self.create_participant(
            learner=learner,
            classs=self.classs,
            datejoined=datetime(2014, 3, 18, 1, 1)
        )

        resp = c.get('%s%s,%s' % (burl, disc.id, disc2.id))
        self.assertContains(resp, 'Respond to Selected')

        resp = c.post('%s%s,%s' % (burl, disc.id, disc2.id),
                      data={
                          'title': '',
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, disc.id, disc2.id),
                      data={
                          'title': '',
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s,%s' % (burl, disc.id, disc2.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, disc.id, disc2.id),
                      data={
                          'title': 'test',
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        disc = Discussion.objects.get(pk=disc.id)
        disc2 = Discussion.objects.get(pk=disc2.id)
        self.assertIsNotNone(disc.response)
        self.assertEquals(disc.response.moderated, True)
        self.assertEquals(disc.response.author, self.admin_user)
        self.assertIsNotNone(disc2.response)
        self.assertEquals(disc2.response.moderated, True)
        self.assertEquals(disc2.response.author, self.admin_user)

    def test_admin_blog_comment_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        burl = '/blog_comment_response/'

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'PostComment 1000 not found')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456788",
            mobile="+27223456788",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        post = self.create_post()
        c1 = self.create_post_comment(post, learner)

        resp = c.get('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'Respond to Blog Comment')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        pc = PostComment.objects.get(pk=c1.id)
        self.assertIsNotNone(pc.response)
        self.assertEquals(pc.response.moderated, True)
        self.assertEquals(pc.response.author, self.admin_user)

        resp = c.get('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'Respond to Blog Comment')

    def test_admin_blog_comment_response_selected(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        burl = '/blog_comment_response_selected/'

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'All the selected Blog Comments have been responded too')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456888",
            mobile="+27223456888",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        post = self.create_post()
        pc1 = self.create_post_comment(post, learner)
        pc2 = self.create_post_comment(post, learner)

        resp = c.get('%s%s,%s' % (burl, pc1.id, pc2.id))
        self.assertContains(resp, 'Respond to Selected')

        resp = c.post('%s%s,%s' % (burl, pc1.id, pc2.id),
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, pc1.id, pc2.id),
                      data={
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s,%s' % (burl, pc1.id, pc2.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, pc1.id, pc2.id),
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        pc1 = PostComment.objects.get(pk=pc1.id)
        pc2 = PostComment.objects.get(pk=pc2.id)
        self.assertIsNotNone(pc1.response)
        self.assertEquals(pc1.response.moderated, True)
        self.assertEquals(pc1.response.author, self.admin_user)
        self.assertIsNotNone(pc2.response)
        self.assertEquals(pc2.response.moderated, True)
        self.assertEquals(pc2.response.author, self.admin_user)
        # because we are posting to the same blog only one reply is made
        self.assertEquals(pc1.response.id, pc2.response.id)

    def test_admin_chat_response(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)
        burl = '/chat_response/'

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'ChatMessage 1000 not found')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456788",
            mobile="+27223456788",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        c1 = self.create_chat_message(self.chat_group, learner)

        resp = c.get('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'Respond to Chat Message')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s' % (burl, c1.id),
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        cm = ChatMessage.objects.get(pk=c1.id)
        self.assertIsNotNone(cm.response)
        self.assertEquals(cm.response.moderated, True)
        self.assertEquals(cm.response.author, self.admin_user)

        resp = c.get('%s%s' % (burl, c1.id))
        self.assertContains(resp, 'Respond to Chat Message')

    def test_admin_chat_response_selected(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        burl = '/chat_response_selected/'

        resp = c.get('%s1000' % burl)
        self.assertContains(resp, 'All the selected Chat Messages have been responded too')

        learner = self.create_learner(
            self.school,
            first_name="jan",
            username="+27223456888",
            mobile="+27223456888",
            country="country",
            area="Test_Area",
            unique_token='abc123',
            unique_token_expiry=datetime.now() + timedelta(days=30),
            is_staff=True
        )

        c1 = self.create_chat_message(self.chat_group, learner)
        c2 = self.create_chat_message(self.chat_group, learner)

        resp = c.get('%s%s,%s' % (burl, c1.id, c2.id))
        self.assertContains(resp, 'Respond to Selected')

        resp = c.post('%s%s,%s' % (burl, c1.id, c2.id),
                      data={
                          'publishdate_0': '',
                          'publishdate_1': '',
                          'content': ''
                      })
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, c1.id, c2.id),
                      data={
                          'publishdate_0': '2015-33-33',
                          'publishdate_1': '99:99:99',
                          'content': ''
                      })
        self.assertContains(resp, 'Please enter a valid date and time.')

        resp = c.post('%s%s,%s' % (burl, c1.id, c2.id))
        self.assertContains(resp, 'This field is required.')

        resp = c.post('%s%s,%s' % (burl, c1.id, c2.id),
                      data={
                          'publishdate_0': '2014-01-01',
                          'publishdate_1': '00:00:00',
                          'content': '<p>Test</p>'
                      })

        c1 = ChatMessage.objects.get(pk=c1.id)
        c2 = ChatMessage.objects.get(pk=c2.id)
        self.assertIsNotNone(c1.response)
        self.assertEquals(c1.response.moderated, True)
        self.assertEquals(c1.response.author, self.admin_user)
        self.assertIsNotNone(c2.response)
        self.assertEquals(c2.response.moderated, True)
        self.assertEquals(c2.response.author, self.admin_user)
        # because we are posting to the same chat group only one reply is made
        self.assertEquals(c1.response.id, c2.response.id)

    def admin_page_test_helper(self, c, page):
        resp = c.get(page)
        self.assertEquals(resp.status_code, 200)

    def test_auth_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/")

        self.admin_page_test_helper(c, "/admin/auth/")
        self.admin_page_test_helper(c, "/admin/auth/coursemanager/")
        self.admin_page_test_helper(c, "/admin/auth/coursementor/")
        self.admin_page_test_helper(c, "/admin/auth/group/")
        self.admin_page_test_helper(c, "/admin/auth/learner/")
        self.admin_page_test_helper(c, "/admin/auth/learner/?tf=1")
        self.admin_page_test_helper(c, "/admin/auth/teacher/")
        self.admin_page_test_helper(c, "/admin/auth/schoolmanager/")
        self.admin_page_test_helper(c, "/admin/auth/systemadministrator/")

    def test_communication_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/communication/")
        self.admin_page_test_helper(c, "/admin/communication/ban/")
        self.admin_page_test_helper(c, "/admin/communication/chatgroup/")
        self.admin_page_test_helper(c, "/admin/communication/chatmessage/")
        self.admin_page_test_helper(c, "/admin/communication/discussion/")
        self.admin_page_test_helper(c, "/admin/communication/message/")
        self.admin_page_test_helper(c, "/admin/communication/moderation/")
        self.admin_page_test_helper(c, "/admin/communication/postcomment/")
        self.admin_page_test_helper(c, "/admin/communication/post/")
        self.admin_page_test_helper(c, "/admin/communication/profanity/")
        self.admin_page_test_helper(c, "/admin/communication/smsqueue/")
        self.admin_page_test_helper(c, "/admin/communication/reportresponse/")
        self.admin_page_test_helper(c, "/admin/communication/report/")
        self.admin_page_test_helper(c, "/admin/communication/sms/")

    def test_content_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/content/")
        self.admin_page_test_helper(c, "/admin/content/learningchapter/")
        self.admin_page_test_helper(c, "/admin/content/mathml/")
        self.admin_page_test_helper(c, "/admin/content/testingquestionoption/")
        self.admin_page_test_helper(c, "/admin/content/testingquestion/")
        self.admin_page_test_helper(c, "/admin/content/goldenegg/")
        self.admin_page_test_helper(c, "/admin/content/goldeneggrewardlog/")
        self.admin_page_test_helper(c, "/admin/content/event/")
        self.admin_page_test_helper(c, "/admin/content/sumit/")
        self.admin_page_test_helper(c, "/admin/content/sumitlevel/")

    def test_core_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/core/")
        self.admin_page_test_helper(c, "/admin/core/class/")
        self.admin_page_test_helper(c, "/admin/core/participantquestionanswer/")
        self.admin_page_test_helper(c, "/admin/core/participant/")

    def test_gamification_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/gamification/")
        self.admin_page_test_helper(c, "/admin/gamification/gamificationbadgetemplate/")
        self.admin_page_test_helper(c, "/admin/gamification/gamificationpointbonus/")
        self.admin_page_test_helper(c, "/admin/gamification/gamificationscenario/")

    def test_organisation_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.admin_page_test_helper(c, "/admin/organisation/")
        self.admin_page_test_helper(c, "/admin/organisation/course/")
        self.admin_page_test_helper(c, "/admin/organisation/module/")
        self.admin_page_test_helper(c, "/admin/organisation/organisation/")
        self.admin_page_test_helper(c, "/admin/organisation/school/")

    def test_results_admin_pages_render(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        self.create_and_answer_questions(2, "_res_w_", datetime.now())
        self.create_and_answer_questions(2, "_res_c_", datetime.now(), True)

        url = "/admin/results/%s" % self.course.id
        self.admin_page_test_helper(c, url)

        resp = c.post(url, data={"state": 1})
        self.assertContains(resp, "Activity")

        resp = c.post(url, data={"state": 2})
        self.assertContains(resp, "q_res_w_0")
        self.assertContains(resp, "q_res_w_1")
        self.assertContains(resp, "q_res_c_0")
        self.assertContains(resp, "q_res_c_1")
        self.assertContains(resp, "( 0% correct )")
        self.assertContains(resp, "( 100% correct )")

        resp = c.post(url, data={"state": 2, "module_filter": self.module.id})
        self.assertContains(resp, "q_res_w_0")
        self.assertContains(resp, "q_res_w_1")
        self.assertContains(resp, "q_res_c_0")
        self.assertContains(resp, "q_res_c_1")
        self.assertContains(resp, "( 0% correct )")
        self.assertContains(resp, "( 100% correct )")

        resp = c.post(url, data={"state": 3})
        self.assertContains(resp, "Class Results")
        self.assertContains(resp, self.classs.name)

    def test_basic_learner_filters(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        url = "/admin/auth/learner/?%s=%s"

        #active filter
        resp = c.get(url % ("acic", "a"))
        self.assertContains(resp, "27123456789")

        lad = self.learner.last_active_date
        self.learner.last_active_date = None
        self.learner.save()

        resp = c.get(url % ("acic", "i"))
        self.assertContains(resp, "27123456789")

        self.learner.last_active_date = lad
        self.learner.save()

        #percentage correct
        resp = c.get(url % ("pc", "0"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "1"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "2"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "3"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "4"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc", "5"))
        self.assertContains(resp, "Learners")

        # no filter number 6 should render 0's data
        resp = c.get(url % ("pc", "6"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pc=0&tf=", "0"))
        self.assertContains(resp, "Learners")

        #percentage completed
        resp = c.get(url % ("pqc", "0"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "1"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "2"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "3"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "4"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "5"))
        self.assertContains(resp, "Learners")

        resp = c.get(url % ("pqc", "6"))
        self.assertContains(resp, "Learners")

        #limiting number of results returned
        for i in range(1, 6):
            self.create_learner(
                self.school,
                username="+2712345678%s" % i,
                mobile="+2712345678%s" % i,
                country="country",
                area="Test_Area",
                is_staff=True)
        resp = c.get(url % ("lmt", "0"))
        self.assertContains(resp, "Learners")

    def test_award_badge(self):
        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        #invalid participant
        resp = c.get(reverse("award.badge", kwargs={'learner_id': 99, 'scenario_id': 99}), follow=True)
        self.assertRedirects(resp, "/admin/auth/learner/")

        #invalid scenario
        resp = c.get(reverse("award.badge", kwargs={'learner_id': self.learner.id, 'scenario_id': 99}), follow=True)
        self.assertRedirects(resp, "/admin/auth/learner/")

        bt = self.create_badgetemplate(
            name="test badge",
            description="test"
        )
        sc = self.create_gamification_scenario(
            name="test scenario",
            course=self.course,
            module=self.module,
            badge=bt,
            event="TEST_EVENT",
            award_type=1
        )

        #get
        resp = c.get(reverse("award.badge", kwargs={'learner_id': self.learner.id, 'scenario_id': sc.id}))
        self.assertEquals(resp.status_code, 200)

        #invalid post
        resp = c.post(reverse("award.badge", kwargs={'learner_id': self.learner.id, 'scenario_id': sc.id}),
                      data={},
                      follow=True)
        self.assertRedirects(resp, "/admin/auth/learner/%s/" % self.learner.id)

        #post first award
        resp = c.post(reverse("award.badge", kwargs={'learner_id': self.learner.id, 'scenario_id': sc.id}),
                      data={'award_yes': 'award_yes'},
                      follow=True)
        self.assertRedirects(resp, "/admin/auth/learner/%s/" % self.learner.id)
        badge_exists = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, scenario=sc).exists()
        self.assertEquals(badge_exists, True)

        #post second award on type 1
        resp = c.post(reverse("award.badge", kwargs={'learner_id': self.learner.id, 'scenario_id': sc.id}),
                      data={'award_yes': 'award_yes'},
                      follow=True)
        self.assertRedirects(resp, "/admin/auth/learner/%s/" % self.learner.id)

        #post second award on type 2
        sc.award_type = 2
        sc.save()
        resp = c.post(reverse("award.badge", kwargs={'learner_id': self.learner.id, 'scenario_id': sc.id}),
                      data={'award_yes': 'award_yes'},
                      follow=True)
        badge = ParticipantBadgeTemplateRel.objects.filter(participant=self.participant, scenario=sc).first()
        self.assertRedirects(resp, "/admin/auth/learner/%s/" % self.learner.id)
        self.assertEquals(badge.awardcount, 2)
