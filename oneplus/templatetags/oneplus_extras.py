from bs4 import BeautifulSoup, NavigableString
from django import template
import re
import bleach
from django.utils.html import remove_tags

register = template.Library()


def format_content(value):
    value = value.replace('</p>', '<br>')
    value = bleach.clean(value, allowed_tags,
                         allowed_attributes,
                         allowed_styles,
                         strip=True)
    soup = BeautifulSoup(value)

    tags = soup.find_all('img')
    for tag in tags:
        if tag is not None:
            if "style" in unicode(tag):
                width = re.findall(r'\d+', tag['style'])
                style = tag['style']
                if width:
                    if int(width[0]) > 280 or style == u'width: 100%;':
                        tag['style'] = 'width:100%;vertical-align:middle'
                    else:
                        tag['style'] = 'width:%spx;vertical-align:middle' \
                                       % width[0]

    if soup.body:
        body = get_content(soup)
        remove_tags(unicode(body), "body")
        output = soup.new_tag("div")
        list = body.contents[:]
        for content in list:
            output.append(content)

    return unicode(output)

register.filter('format_content', format_content)


def format_option(value):

    value = value.replace('</p>', '<br>')
    value = bleach.clean(value, allowed_tags,
                         allowed_attributes,
                         allowed_styles,
                         strip=True)

    soup = BeautifulSoup(value)
    tags = soup.find_all('img')
    if tags:
        for tag in tags:
            tag['style'] = 'vertical-align:middle'

    if soup.body:
        body = get_content(soup)
        output = remove_tags(unicode(body), "body")

    return unicode(output)


register.filter('format_option', format_option)


def get_content(value):
    return value.body.extract()


allowed_tags = ['b', 'i', 'strong', 'em', 'img', 'a', 'br']
allowed_attributes = ['href', 'title', 'style', 'src']
allowed_styles = [
    'font-family',
    'font-weight',
    'text-decoration',
    'font-variant',
    'width',
    'height']