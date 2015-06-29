from dateutil import parser
from datetime import datetime
import re
from auth.models import CustomUser
from core.models import Class
from core.common import PROVINCES
from organisation.models import School
from django.db.models import Q


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

    return False, clean(content)


def validate_to_course(post):
    to_course = None

    if 'to_course' in post:
        to_course = post['to_course']
    else:
        return True, to_course

    return False, to_course


def validate_name(post):
    name = None

    if 'name' in post:
        name = post['name']

        if zero_len(name):
            return True, name
    else:
        return True, name

    return False, name


def validate_course(post):
    to_course = None

    if 'course' in post:
        to_course = post['course']
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


def validate_date_and_time(post):
    date = None
    time = None
    dt = None

    if 'date_sent_0' in post and 'date_sent_1' in post:
        try:
            date = post['date_sent_0']
            time = post['date_sent_1']

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


def validate_message(post):
    message = None

    if 'message' in post:
        message = post['message']

        if zero_len(message):
            return True, message
    else:
        return True, message

    return False, clean(message)


def validate_users(post):
    users = None

    if 'users' in post:
        user_list = post.getlist('users')
        for u in user_list:
            if u == "all" and len(user_list) > 1:
                return True, user_list
            users = user_list
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


def clean(content):
    rep = {"<p>": "", "</p>": "", "<br>": ""}

    rep = dict((re.escape(k), v) for k, v in rep.iteritems())
    pattern = re.compile("|".join(rep.keys()))
    content = pattern.sub(lambda m: rep[re.escape(m.group(0))], content)

    return content


def validate_mobile(mobile):
    pattern_both = "^(\+\d{1,2})?\d{10}$"
    match = re.match(pattern_both, mobile)
    if match:
        return mobile
    else:
        return None


def validate_sign_up_form(post):
    data = {}
    errors = {}

    if "first_name" in post.POST.keys() and post.POST["first_name"]:
        data["first_name"] = post.POST["first_name"]
    else:
        errors["first_name_error"] = "This must be completed"

    if "surname" in post.POST.keys() and post.POST["surname"]:
        data["surname"] = post.POST["surname"]
    else:
        errors["surname_error"] = "This must be completed"

    if "cellphone" in post.POST.keys() and post.POST["cellphone"]:
        cellphone = post.POST["cellphone"]
        if validate_mobile(cellphone):
            if CustomUser.objects.filter(Q(mobile=cellphone) | Q(username=cellphone)).exists():
                errors["cellphone_error"] = "registered"
            else:
                data["cellphone"] = cellphone
        else:
            errors["cellphone_error"] = "Enter a valid cellphone number"
    else:
        errors["cellphone_error"] = "This must be completed"

    if "grade" in post.POST.keys() and post.POST["grade"]:
        if post.POST["grade"] not in ("Grade 10", "Grade 11"):
            errors["grade_error"] = "Select your grade"
        else:
            data["grade"] = post.POST["grade"]
    else:
        errors["grade_error"] = "This must be completed"

    if "province" in post.POST.keys() and post.POST["province"]:
        if post.POST["province"] in PROVINCES:
            data["province"] = post.POST["province"]
        else:
            errors["province_error"] = "Select your province"
    else:
        errors["province_error"] = "Select your province"

    if "enrolled" in post.POST.keys() and post.POST["enrolled"]:
        data["enrolled"] = post.POST["enrolled"]
    else:
        errors["enrolled_error"] = "This must be completed"

    return data, errors


def validate_sign_up_form_promath(post):
    data = {}
    errors = {}

    if "school" in post.POST.keys() and post.POST["school"]:
        try:
            School.objects.get(id=post.POST["school"])
            data["school"] = post.POST["school"]
        except School.DoesNotExist:
            errors["school_error"] = "Select your school"
    else:
        errors["school_error"] = "This must be completed"

    if "classs" in post.POST.keys() and post.POST["classs"]:
        try:
            Class.objects.get(id=post.POST["classs"])
            data["classs"] = post.POST["classs"]
        except Class.DoesNotExist:
            errors["classs_error"] = "Select your class"
    else:
        errors["classs_error"] = "This must be completed"

    return data, errors