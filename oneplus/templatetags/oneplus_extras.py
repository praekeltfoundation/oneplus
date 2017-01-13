from bs4 import BeautifulSoup, NavigableString
from django import template
import re
import bleach
from django.utils.html import remove_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

register = template.Library()


def format_content(value):
    value = value.replace('</p>', '<br>')
    value = bleach.clean(value, allowed_tags,
                         allowed_attributes,
                         allowed_styles,
                         strip=True)

    value = unicode(value)
    while value.endswith('<br>'):
        value = value[:-4]

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

    value = unicode(value)
    while value.endswith('<br>'):
        value = value[:-4]

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


@register.filter(name='ordinal_extra', is_safe=True)
def ordinal_extra(value, flag=None):
    """
    Converts an integer to its ordinal as a string. 1 is '1st', 2 is '2nd',
    3 is '3rd', etc. Works for any integer.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    suffixes = (_('th'), _('st'), _('nd'), _('rd'), _('th'), _('th'), _('th'), _('th'), _('th'), _('th'))
    if value % 100 in (11, 12, 13):  # special case
        return mark_safe("%d%s" % (value, suffixes[0]))
    # Mark value safe so i18n does not break with <sup> or <sub> see #19988
    if flag == 'sup':
        return mark_safe("%d<sup>%s</sup>" % (value, suffixes[value % 10]))
    return mark_safe("%d%s" % (value, suffixes[value % 10]))
