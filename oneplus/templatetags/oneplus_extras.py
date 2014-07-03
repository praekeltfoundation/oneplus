from bs4 import BeautifulSoup
from django import template

register = template.Library()

def format_width(value):
    soup = BeautifulSoup(value)
    tags = soup.find_all('img')
    for tag in tags:
        if tag is not None:
            tag['style'] = 'width:100%'

    return soup

register.filter('format_width', format_width)
