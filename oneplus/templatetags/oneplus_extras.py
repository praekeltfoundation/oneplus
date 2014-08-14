from bs4 import BeautifulSoup, NavigableString
from django import template
import re

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

    return soup

register.filter('format_width', format_width)


def align(value):
    soup = value
    tags = soup.find_all('img')
    if tags:
        for tag in tags:
            tag['style'] = 'vertical-align:middle'
            return tag
    else:
        return soup

register.filter('align', align)


def strip_tags(value):
    soup = BeautifulSoup(value)

    tags = soup.findAll(True)
    if tags:
        for tag in tags:
            if tag.name in invalid_tags:
                s = ""

                for c in tag.contents:
                    if not isinstance(c, NavigableString):
                        c = strip_tags(unicode(c))
                    s += unicode(c)

                tag.replaceWith(s)
        return soup
    else:
        return soup

invalid_tags = ['p', 'br']

register.filter('strip_tags', strip_tags)