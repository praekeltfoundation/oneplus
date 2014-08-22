from bs4 import BeautifulSoup
import re
from django.utils.html import remove_tags


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


def align(value):

    soup = BeautifulSoup(value)
    tags = soup.find_all('img')
    if tags:
        for tag in tags:
            tag['style'] = 'vertical-align:middle'
    if soup.body:
        body = get_content(soup)
        return body_to_div(body, soup)
    else:
        return value


def strip_tags(value):
    content = remove_tags(value, "p")
    return u'%s' % content


def get_content(value):
    return value.body.extract()


def body_to_div(body, soup):
    remove_tags(str(body), "body")
    output = soup.new_tag("div")
    list = body.contents[:]
    for content in list:
        output.append(content)
        output['style'] = \
            'vertical-align:middle;display:inline-block;width:80%'

    return u'%s' % output
