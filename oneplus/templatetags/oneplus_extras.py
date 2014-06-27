from bs4 import BeautifulSoup
from django import template

register = template.Library()

def format_width(value):
    soup = BeautifulSoup(value)
    tag = soup.img
    tag['style'] = 'width:100%'
    return tag

register.filter('format_width', format_width)
