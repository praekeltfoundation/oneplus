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
    content = None

    if 'content' in post:
        content = post['content']

        if zero_len(content):
            return True, content
    else:
        return True, content

    return False, content