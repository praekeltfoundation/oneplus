# -*- coding: utf-8 -*-
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test.client import Client
from utils import format_option, format_content
from communication.models import ChatMessage, Discussion, PostComment, ChatGroup, Post
from organisation.models import Course
from auth.models import CustomUser
from datetime import datetime


class TestContent(TestCase):

    def test_strip_p_tags(self):
        content = "<p><b>Test</b></p>"
        result = format_content(content)
        self.assertEquals(result, "<div><b>Test</b><br/></div>")

    def test_align_image_only(self):
        content = "<img/>"
        result = format_option(content)
        self.assertEquals(result, u'<img style="vertical-align:middle"/>')

    def test_format_option_text_only(self):
        content = "Test"
        result = format_option(content)
        self.assertEquals(result, u'Test')

    def test_format_option_text_and_image(self):
        content = "<b>Test</b><img/>"
        result = format_option(content)
        self.assertEquals(result, u'<b>Test</b><img style='
                                  u'"vertical-align:middle"/>')

    def test_format_option_double_image(self):
        content = "<img/><img/>"
        result = format_option(content)
        self.assertEquals(result, u'<img style="vertical-align:middle"/>'
                                  u'<img style="vertical-align:middle"/>')

    def test_format_option(self):
        content = "<b>Test</b><p></p><img/>"
        output = format_option(content)
        self.assertEquals(output, u'<b>Test</b><br/><img style="'
                                  u'vertical-align:middle"/>')

    def test_format_content(self):
        content = '<img style="width:300px"/>'
        result = format_content(content)
        self.assertEquals(result, u'<div><img style="width:100%;'
                                  u'vertical-align:middle"/></div>')

    def test_already_format_content(self):
        content = '<img style="width:100%"/>'
        result = format_content(content)
        self.assertEquals(result, u'<div><img style="width:100%;'
                                  u'vertical-align:middle"/></div>')

    def test_format_content_small_image(self):
        content = '<img style="width:60px"/>'
        result = format_content(content)
        self.assertEquals(result, u'<div><img style="width:60px;'
                                  u'vertical-align:middle"/></div>')

    def test_filters_empty(self):
        content = ""
        output = format_content(content)
        self.assertEquals(output, u'<div></div>')

    def test_filters_empty_option(self):
        content = ""
        output = format_option(content)
        self.assertEquals(output, u'')

    def test_unicode_input(self):
        content = u'Zoë'
        output = format_option(content)
        self.assertEquals(output, u'Zoë')


class TestPublishViews(TestCase):

    def create_user(self, mobile="+27123456789", country="country", **kwargs):
        model_class = get_user_model()
        return model_class.objects.create(
            mobile=mobile, country=country, **kwargs)

    def create_chatgroup(self, name='TestGroup', description='TestGroup'):
        return ChatGroup.objects.create(
            name=name,
            description=description
        )

    def create_chatmessage(self, content):
        return ChatMessage.objects.create(
            chatgroup=self.chatgroup,
            author=self.user,
            content=content,
            publishdate=datetime.now()
        )

    def create_discussion(self, content, name='Test', description='Test'):
        return Discussion.objects.create(
            name=name,
            description=description,
            content=content,
            author=self.user,
            publishdate=datetime.now()
        )

    def create_course(self, name='Test', description='Test', slug='Test'):
        return Course.objects.create(
            name=name,
            description=description,
            slug=slug
        )

    def create_post(self, content, name='Test', description='Test'):
        return Post.objects.create(
            name=name,
            description=description,
            course=self.course,
            content=content,
            publishdate=datetime.now()
        )

    def create_postcomment(self, post, content):
        return PostComment.objects.create(
            post=post,
            content=content,
            author=self.user,
            publishdate=datetime.now()
        )

    def setUp(self):
        self.user = self.create_user()
        self.chatgroup = self.create_chatgroup()
        self.course = self.create_course()
        self.post = self.create_post('Test Test Test Test')
        self.admin_user_password = 'mypassword'
        self.admin_user = CustomUser.objects.create_superuser(
            username='asdf33',
            email='asdf33@example.com',
            password=self.admin_user_password,
            mobile='+27111111133')

    def test_chatmessage_publish_unpublish(self):
        cm = self.create_chatmessage('Test Test test')

        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        base_url = '/admin/communication/chatmessage/publish/'

        url = base_url + '10000'
        resp = c.get(url)
        self.assertContains(resp, 'Can''t find record')

        url = base_url + str(cm.pk)
        resp = c.get(url)
        self.assertContains(resp, 'ChatMessage has been published')

        cm = ChatMessage.objects.get(pk=cm.pk)
        self.assertEquals(cm.moderated, True)

        base_url = '/admin/communication/chatmessage/unpublish/'
        url = base_url + '10000'
        resp = c.get(url)
        self.assertContains(resp, 'Can''t find record')

        url = base_url + str(cm.pk)
        resp = c.get(url)
        self.assertContains(resp, 'ChatMessage has been unpublished')

        cm = ChatMessage.objects.get(pk=cm.pk)
        self.assertEquals(cm.moderated, False)
        self.assertEquals(cm.unmoderated_by.username, self.admin_user.username)
        self.assertIsNotNone(cm.unmoderated_date)

    def test_discussion_publish_unpublish(self):
        d = self.create_discussion('Test Test test')

        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        base_url = '/admin/communication/discussion/publish/'

        url = base_url + '10000'
        resp = c.get(url)
        self.assertContains(resp, 'Can''t find record')

        url = base_url + str(d.pk)
        resp = c.get(url)
        self.assertContains(resp, 'Discussion has been published')

        d = Discussion.objects.get(pk=d.pk)
        self.assertEquals(d.moderated, True)

        base_url = '/admin/communication/discussion/unpublish/'
        url = base_url + '10000'
        resp = c.get(url)
        self.assertContains(resp, 'Can''t find record')

        url = base_url + str(d.pk)
        resp = c.get(url)
        self.assertContains(resp, 'Discussion has been unpublished')

        d = Discussion.objects.get(pk=d.pk)
        self.assertEquals(d.moderated, False)
        self.assertEquals(d.unmoderated_by.username, self.admin_user.username)
        self.assertIsNotNone(d.unmoderated_date)

    def test_postcomment_publish_unpublish(self):
        pc = self.create_postcomment(self.post, 'Test Test test')

        c = Client()
        c.login(username=self.admin_user.username, password=self.admin_user_password)

        base_url = '/admin/communication/postcomment/publish/'

        url = base_url + '10000'
        resp = c.get(url)
        self.assertContains(resp, 'Can''t find record')

        url = base_url + str(pc.pk)
        resp = c.get(url)
        self.assertContains(resp, 'PostComment has been published')

        pc = PostComment.objects.get(pk=pc.pk)
        self.assertEquals(pc.moderated, True)

        base_url = '/admin/communication/postcomment/unpublish/'
        url = base_url + '10000'
        resp = c.get(url)
        self.assertContains(resp, 'Can''t find record')

        url = base_url + str(pc.pk)
        resp = c.get(url)
        self.assertContains(resp, 'PostComment has been unpublished')

        pc = PostComment.objects.get(pk=pc.pk)
        self.assertEquals(pc.moderated, False)
        self.assertEquals(pc.unmoderated_by.username, self.admin_user.username)
        self.assertIsNotNone(pc.unmoderated_date)


class AdminSiteTests(TestCase):

    def setUp(self):
        self.admin_user_password = 'mypassword'
        self.admin_user = CustomUser.objects.create_superuser(
            username='asdf33',
            email='asdf33@example.com',
            password=self.admin_user_password,
            mobile='+27111111133')

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