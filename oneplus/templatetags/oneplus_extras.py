from bs4 import BeautifulSoup, NavigableString
from django import template
import re
from django.utils.html import remove_tags

register = template.Library()


def format_width(value):
    soup = BeautifulSoup(value)
    tags = soup.find_all('img')
    for tag in tags:
            if tag is not None:
                if "style" in str(tag):
                    width = re.findall(r'\d+', tag['style'])
                    if width:
                        if int(width[0]) > 280:
                            tag['style'] = 'width:100%'

    if soup.body:
        body = get_content(soup)
    return unicode(body)

register.filter('format_width', format_width)


def align(value):

    soup = BeautifulSoup(value)

    if soup.body:
        body = get_content(soup)
        remove_bodytags(body)
        output = soup.new_tag("div")
        list = body.contents[:]
        for content in list:
            output.append(content)
        output['style'] = \
            'vertical-align:middle;display:inline-block;width:80%'

    return u'%s' % output

register.filter('align', align)


def strip_tags(value):
    content = remove_tags(value, "p")
    return u'%s' % content


register.filter('strip_tags', strip_tags)


def get_content(value):
    return value.body.extract()


def remove_bodytags(body):
    remove_tags(str(body), "body")

