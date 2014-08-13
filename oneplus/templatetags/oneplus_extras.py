from bs4 import BeautifulSoup
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
    soup = BeautifulSoup(value)
    tags = soup.find_all('img')
    if tags:
        for tag in tags:
            tag['style'] = 'vertical-align:middle'
            return tag
    else:
        return soup

register.filter('align', align)