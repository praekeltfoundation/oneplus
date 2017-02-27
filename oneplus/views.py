from __future__ import division
from datetime import date
from functools import wraps
import json
from django.shortcuts import HttpResponse, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from communication.utils import contains_profanity, get_replacement_content
from report_utils import get_csv_report, get_xls_report
from django.core.urlresolvers import reverse
from core.stats import question_answered, question_answered_correctly, percentage_question_answered_correctly
from organisation.models import Course
from content.models import TestingQuestion
from core.models import Class, Learner, Participant

COUNTRYWIDE = "Countrywide"


# Code decorator to ensure that the user is logged in
def oneplus_login_required(f):
    @oneplus_state_required
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if "user" not in request.session.keys():
            return redirect("auth.login")
        else:
            user = request.session["user"]
            if Learner.objects.filter((Q(enrolled='0') | Q(grade=None) | Q(grade='')) & Q(id=user['id'])).exists():
                return redirect("auth.return_signup")
        return f(request, user=user, *args, **kwargs)
    return wrap


# Code decorator to ensure that view state exists and is properly handled
def oneplus_state_required(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        # Initialise the oneplus state
        # If value is 0, the user's session cookie will expire when the user's
        # Web browser is closed.
        request.session.set_expiry(31536000)
        if "state" not in request.session.keys():
            request.session["state"] = {"menu_visible": False}

        # Manage menu state
        if request.method == "POST" and "switchmenu" in request.POST:
            request.session["state"]["menu_visible"] \
                = request.POST["switchmenu"] != 'True'
        else:
            request.session["state"]["menu_visible"] = False

        return f(request, state=request.session["state"], *args, **kwargs)
    return wrap


def oneplus_participant_required(f):
    @oneplus_login_required
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if "participant_id" in request.session["user"]:
            try:
                participant = Participant.objects.get(pk=request.session["user"]["participant_id"], is_active=True)
            except Participant.DoesNotExist:
                request.session.flush()
                return redirect("auth.login")
            return f(request, participant=participant, *args, **kwargs)
    return wrap


def oneplus_check_user(f):
    @oneplus_state_required
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if "user" in request.session.keys():
            return f(request, user=request.session["user"], *args, **kwargs)
        else:
            return f(request, user=None, *args, **kwargs)
    return wrap


def get_week_day():
    home_day = date.today().weekday()
    if home_day == 5 or home_day == 6:
        home_day = 0
    return home_day


@user_passes_test(lambda u: u.is_staff)
def question_difficulty_report(request, mode):
    questions = TestingQuestion.objects.all()
    question_list = []
    headers = [('Question', 'Total Correct', 'Total Incorrect', 'Percentage Correct')]

    for question in questions:
        total_answers = question_answered(question)
        total_correct = question_answered_correctly(question)
        total_incorrect = total_answers - total_correct
        percent_correct = percentage_question_answered_correctly(question)

        question_list.append((question.name, total_correct, total_incorrect, percent_correct))

    question_list = sorted(question_list, key=lambda x: (-x[2], -x[3]))
    if mode == '1':
        return get_csv_report(question_list, 'question_difficulty_report', headers)
    elif mode == '2':
        return get_xls_report(question_list, 'question_difficulty_report', headers)
    else:
        return HttpResponseRedirect(reverse("reports.home"))


@user_passes_test(lambda u: u.is_staff)
def get_users(request):
    classs = request.GET.get('class', 'all')
    only_active = request.GET.get('only_active', None)

    learners = Learner.objects.filter(is_active=True)
    if only_active:
        learners = learners.filter(participant__is_active=True)

    if classs != 'all':
        try:
            classs = int(classs)

            current_class = Class.objects.get(id=classs)
            if current_class:
                current_class = Class.objects.get(id=classs)
                learners = learners.filter(participant__classs_id=current_class.id)
        except (ValueError, Class.DoesNotExist):
            learners = None

    data = []
    if learners:
        data = [{"id": l['id'], "name": l['mobile']} for l in learners.values('id', 'mobile').distinct('id')]

    return HttpResponse(json.dumps(data), content_type="application/javascript")


def get_courses(request):
    courses = Course.objects.all()

    data = []
    for c in courses:
        line = {"id": c.id, "name": c.name}
        data.append(line)

    return HttpResponse(json.dumps(data), content_type="application/javascript")


def get_classes(request, course):
    if course == 'all':
        classes = Class.objects.all()
    else:
        try:
            course = int(course)
            current_course = Course.objects.get(id=course)
            classes = Class.objects.all().filter(course=current_course)
        except (ValueError, Course.DoesNotExist):
            classes = None

    data = []
    if classes:
        for c in classes:
            line = {"id": c.id, "name": c.name}
            data.append(line)

    return HttpResponse(json.dumps(data), content_type="application/javascript")


def _content_profanity_check(obj):
    if contains_profanity(obj.content):
        obj.original_content = obj.content
        obj.content = get_replacement_content(profanity=True)
        obj.save()
        return True
    else:
        return False
