from django.test import TestCase
from utils import strip_tags, align, format_width


class TestContent(TestCase):

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