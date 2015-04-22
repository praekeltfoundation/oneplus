from dateutil import parser
from datetime import datetime


def zero_len(value):
        return len(value.strip()) == 0


def gen_username(user):
    un = '%s %s' % (user.first_name, user.last_name)

    if zero_len(un):
        return user.username
    else:
        return un


def validate_title(post):
    title = None

    if 'title' in post:
        title = post['title']

        if zero_len(title):
            return True, title
    else:
        return True, title

    return False, title


def validate_publish_date_and_time(post):
    date = None
    time = None
    dt = None

    if 'publishdate_0' in post and 'publishdate_1' in post:
        try:
            date = post['publishdate_0']
            time = post['publishdate_1']

            if zero_len(date) or zero_len(time):
                return True, date, time, dt
            else:
                dt = parser.parse(date + ' ' + time, default=datetime(1970, 2, 1))
                if dt.year == 1970 and dt.month == 2 and dt.day == 1:
                    return True, date, time, dt

        except ValueError:
            return True, date, time, dt
    else:
        return True, date, time, dt

    return False, date, time, dt


def validate_content(post):
    content = ""

    if 'content' in post:
        content = post['content']

        if zero_len(content):
            return True, content
    else:
        return True, content

    return False, content


def validate_name(post):
    name = None

    if 'name' in post:
        name = post['name']

        if zero_len(name):
            return True, name
    else:
        return True, name

    return False, name


def validate_to_course(post):
    to_course = None

    if 'to_course' in post:
        to_course = post['to_course']
    else:
        return True, to_course

    return False, to_course


def validate_to_class(post):
    to_class = None

    if 'to_class' in post:
        to_class = post['to_class']
    else:
        return True, to_class

    return False, to_class


def validate_users(post):
    users = None

    if 'users' in post:
        users = post['users']
    else:
        return True, users

    return False, users


def validate_direction(post):
    direction = None

    if 'direction' in post:
        direction = post['direction']
    else:
        return True, direction

    return False, direction