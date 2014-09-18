# -*- coding: utf-8 -*-
from django.test import TestCase
from utils import format_option, format_content


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