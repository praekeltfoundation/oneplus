from bs4 import BeautifulSoup
from django import template

register = template.Library()

def format_width(value):
    soup = BeautifulSoup(value)
    if soup.img is not None:
        soup.img['style'] = 'width:100%'
    return soup

register.filter('format_width', format_width)
