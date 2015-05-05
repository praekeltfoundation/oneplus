# -*- coding: utf-8 -*-
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test.client import Client
from utils import format_option, format_content
from communication.models import ChatMessage, Discussion, PostComment, ChatGroup
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
        self.assertEquals(result,u'Test')

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

    def setUp(self):
        self.user = self.create_user()
        self.chatgroup = self.create_chatgroup()
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
        self.assertEquals(cm.unmoderated_by__username, self.admin_user.username)
        self.assertIsNotNone(cm.unmoderated_date)