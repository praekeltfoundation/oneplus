from __future__ import division
from django.contrib.auth.models import AbstractBaseUser
from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, logout
from .forms import LoginForm, SmsPasswordForm
from django.core.mail import mail_managers, BadHeaderError
from communication.models import *
from core.models import *
from oneplus.models import *
from datetime import *
from datetime import timedelta
from auth.models import CustomUser
from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from communication.utils import VumiSmsApi
from random import randint
from communication.utils import get_autologin_link
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password
from oneplus.utils import update_metric
from lockout import LockedOut
from django.core.urlresolvers import reverse
from django.db import connection
import oneplusmvp.settings as settings
import koremutake
import json
from report_utils import get_csv_report, get_xls_report
from django.core.urlresolvers import reverse
from core.stats import question_answered, question_answered_correctly, percentage_question_answered_correctly
from dateutil import parser
from .validators import *


COUNTRYWIDE = "Countrywide"


# Code decorator to ensure that the user is logged in
def oneplus_login_required(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if "user" not in request.session.keys():
            return redirect("auth.login")
        return f(request, user=request.session["user"], *args, **kwargs)
    return wrap


# Code decorator to check if user is logged in or not
def oneplus_check_user(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if "user" in request.session.keys():
            return f(request, user=request.session["user"], *args, **kwargs)
        else:
            return f(request, user=None, *args, **kwargs)
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


# Action resolver to elegantly handle verbs in the views
def resolve_http_method(request, methods):
    if isinstance(methods, list):
        methods = dict([(func.__name__.lower(), func) for func in methods])
    if request.method.lower() not in methods.keys():
        return HttpResponse(status=501)
    return methods[request.method.lower()]()


def is_registered(user):
    # Check learner is registered
    return Participant.objects.filter(learner=user.learner).latest('datejoined')


def save_user_session(request, registered, user):

    request.session["user"] = {}
    request.session["user"]["id"] = user.learner.id
    request.session["user"]["name"] = user.learner.first_name
    request.session["user"]["participant_id"] \
        = registered.id
    request.session["user"]["place"] = 0  # TODO
    registered.award_scenario("LOGIN", None)

    # update last login date
    user.last_login = datetime.now()
    user.save()


# Login Screen
@oneplus_state_required
def login(request, state):
    def get():
        return render(request, "auth/login.html", {"state": state,
                                                   "form": LoginForm()})

    def post():
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                # Check if this is a registered user
                user = authenticate(
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"]
                )
            except LockedOut:
                request.session["user_lockout"] = True
                return redirect("auth.getconnected")

            # Check if user is registered
            exists = CustomUser.objects.filter(
                username=form.cleaned_data["username"]
            ).exists()
            request.session["user_exists"] = exists

            if user is not None and user.is_active:
                try:
                    registered = is_registered(user)
                    if registered is not None:
                        save_user_session(request, registered, user)

                        usr = Learner.objects.filter(username=form.cleaned_data["username"])
                        par = Participant.objects.filter(learner=usr)

                        if ParticipantQuestionAnswer.objects.filter(participant=par).count() == 0:
                            return redirect("learn.first_time")
                        else:
                            return redirect("learn.home")
                    else:
                        return redirect("auth.getconnected")
                except ObjectDoesNotExist:
                    request.session["wrong_password"] = False
                    return redirect("auth.getconnected")
            else:
                # Save provided username
                request.session["user_lockout"] = False
                request.session["username"] = form.cleaned_data["username"]
                request.session["wrong_password"] = True
                return redirect("auth.getconnected")
        else:
            return get()

    return resolve_http_method(request, [get, post])


def autologin(request, token):
    def get():
        # Get user based on token + expiry date
        user = CustomUser.objects.filter(
            unique_token__startswith=token,
            unique_token_expiry__gte=datetime.now()
        ).first()
        if user:
            # Login the user
            if user is not None and user.is_active:
                try:
                    registered = is_registered(user)
                    if registered is not None:
                        save_user_session(request, registered, user)
                        return redirect("learn.home")
                    else:
                        return redirect("auth.getconnected")
                except ObjectDoesNotExist:
                    return redirect("auth.login")

        # If token is not valid, render login screen
        return render(
            request,
            "auth/login.html",
            {
                "state": None,
                "form": LoginForm()
            }
        )

    def post():
        return HttpResponseRedirect("/")

    return resolve_http_method(request, [get, post])


# Signout Function
@oneplus_state_required
def signout(request, state):
    logout(request)

    def get():
        return HttpResponseRedirect("/")

    def post():
        return HttpResponseRedirect("/")

    return resolve_http_method(request, [get, post])


# SMS Password Screen
@oneplus_state_required
def smspassword(request, state):
    def get():
        return render(
            request,
            "auth/smspassword.html",
            {
                "state": state,
                "form": SmsPasswordForm()
            }
        )

    def post():
        form = SmsPasswordForm(request.POST)
        if form.is_valid():
            # Initialize vumigo sms
            vumi = VumiSmsApi()

            try:
                # Lookup user
                learner = Learner.objects\
                    .get(username=form.cleaned_data["msisdn"])

                # Generate password
                password = koremutake.encode(randint(10000, 100000))
                learner.password = make_password(password)

                # Message
                message = "Your new password for OnePlus is '|password|' " \
                          "or use the following link to login: |autologin|"

                # Generate autologin link
                learner.generate_unique_token()

                sms, sent = vumi.send(
                    learner.username,
                    message=message,
                    password=password,
                    autologin=get_autologin_link(learner.unique_token)
                )

                if sent:
                    message = "Your new password has been SMSed to you. "
                    success = True
                else:
                    message = "Oops! Something went wrong! " \
                              "Please try enter your number again or "

                    success = False
                learner.save()

                return render(
                    request,
                    "auth/smspassword.html",
                    {
                        "state": state,
                        "sent": True,
                        "message": message,
                        "success": success
                    }
                )

            except ObjectDoesNotExist:
                return HttpResponseRedirect("getconnected")

            return render(request, "auth/smspassword.html", {"state": state})
        else:
            form = SmsPasswordForm()

        return render(
            request,
            "auth/smspassword.html",
            {"state": state, "form": form}
        )

    return resolve_http_method(request, [get, post])


# Get Connected Screen
@oneplus_state_required
def getconnected(request, state):
    def get():
        exists = False
        username = None
        wrong_password = False
        user_lockout = False
        if "user_exists" in request.session:
            exists = request.session["user_exists"]
        if "username" in request.session:
            username = request.session["username"]
        if "wrong_password" in request.session:
            wrong_password = request.session["wrong_password"]
        if "user_lockout" in request.session:
            user_lockout = request.session["user_lockout"]
        return render(
            request,
            "auth/getconnected.html",
            {
                "state": state,
                "exists": exists,
                "provided_username": username,
                "wrong_password": wrong_password,
                "user_lockout": user_lockout
            }
        )

    def post():
        exists = False
        if "user_exists" in request.session:
            exists = request.session["user_exists"]
        if "username" in request.session:
            username = request.session["username"]
        return render(
            request,
            "auth/getconnected.html",
            {
                "state": state,
                "exists": exists,
                "provided_username": username
            }
        )

    return resolve_http_method(request, [get, post])


# Welcome Screen
@oneplus_state_required
def welcome(request, state):
    def get():
        return render(request, "misc/welcome.html", {"state": state})

    def post():
        return render(request, "misc/welcome.html", {"state": state})

    return resolve_http_method(request, [get, post])


def get_week_day():
    home_day = date.today().weekday()
    if home_day == 5 or home_day == 6:
        home_day = 0
    return home_day


# First Time Log in Screen
@oneplus_state_required
@oneplus_login_required
def first_time(request, state, user):
    def get():
        return render(request, "misc/first_time.html", {"state": state,
                                                        "user": user})

    def post():
        return render(request, "misc/first_time.html", {"state": state,
                                                        "user": user})

    return resolve_http_method(request, [get, post])


# FAQ Screen
@oneplus_state_required
@oneplus_login_required
def faq(request, state, user):
    def get():
        return render(request, "misc/faq.html", {"state": state,
                                                 "user": user})

    def post():
        return render(request, "misc/faq.html", {"state": state,
                                                 "user": user})

    return resolve_http_method(request, [get, post])


#Terms Screen
@oneplus_state_required
@oneplus_login_required
def terms(request, state, user):
    def get():
        return render(request, "misc/terms.html", {"state": state,
                                                   "user": user})

    def post():
        return render(request, "misc/terms.html", {"state": state,
                                                   "user": user})

    return resolve_http_method(request, [get, post])


# Home Screen
@oneplus_state_required
@oneplus_login_required
def home(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _start_of_week = date.today() - timedelta(date.today().weekday())
    learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()
    if learnerstate is None:
        learnerstate = LearnerState(participant=_participant)

    answered = ParticipantQuestionAnswer.objects.filter(
        participant=learnerstate.participant
    ).distinct().values_list('question')

    questions = TestingQuestion.objects.filter(
        module__in=learnerstate.participant.classs.course.modules.all(),
        module__is_active=True,
    ).exclude(id__in=answered)

    learner = learnerstate.participant.learner

    if not questions:
        request.session["state"]["questions_complete"] = True
        subject = ' '.join([
            'Questions Completed -',
            learner.first_name,
            learner.last_name,
            '-',
            learner.username
        ])
        message = '\n'.join([
            'Questions completed',
            'Student: ' + learner.first_name + ' ' + learner.last_name,
            'Msisdn: ' + learner.username
        ])

        mail_managers(
            subject=subject,
            message=message,
            fail_silently=False
        )

    else:
        request.session["state"]["questions_complete"] = False

    request.session["state"]["home_points"] = _participant.points
    request.session["state"]["home_badges"] \
        = ParticipantBadgeTemplateRel.objects\
        .filter(participant=_participant)\
        .count()
    request.session["state"]["home_position"]\
        = Participant.objects.filter(
            classs=_participant.classs,
            points__gt=_participant.points
        ).count() + 1

    # Force week day to be Monday, when Saturday or Sunday
    request.session["state"]["home_day"] = learnerstate.get_week_day()

    request.session["state"]["home_tasks_today"]\
        = ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).count()

    request.session["state"]["home_tasks_week"]\
        = learnerstate.get_questions_answered_week()

    request.session["state"]["home_required_tasks"]\
        = learnerstate.get_total_questions()

    request.session["state"]["home_tasks"]\
        = ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=_start_of_week
        ).count()
    request.session["state"]["home_correct"]\
        = ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            correct=True,
            answerdate__gte=_start_of_week
        ).count()
    request.session["state"]["home_goal"]\
        = settings.ONEPLUS_WIN_REQUIRED\
        - request.session["state"]["home_correct"]

    def get():
        _learner = Learner.objects.get(id=user['id'])
        if _learner.last_active_date is None:
            _learner.last_active_date = datetime.now() - timedelta(days=33)

        last_active = _learner.last_active_date.date()
        now = datetime.now().date()
        days_ago = now - last_active

        if days_ago >= timedelta(days=1):
            _learner.last_active_date = datetime.now()
            _learner.save()
            update_metric("running.active.participants24", 1, "SUM")
        if days_ago >= timedelta(days=32):
            update_metric("running.active.participantsmonth", 1, "SUM")
        if days_ago >= timedelta(days=7):
            update_metric("running.active.participants7", 1, "SUM")
        if days_ago >= timedelta(days=2):
                update_metric("running.active.participants48", 1, "SUM")

        return render(request, "learn/home.html", {"state": state,
                                                   "user": user})

    def post():
        return render(request, "learn/home.html", {"state": state,
                                                   "user": user})

    return resolve_http_method(request, [get, post])


# Next Challenge Screen
@oneplus_state_required
@oneplus_login_required
def nextchallenge(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant__id=user["participant_id"]
    ).first()
    if _learnerstate is None:
        _learnerstate = LearnerState(participant=_participant)

    # check if new question required then show question
    _learnerstate.getnextquestion()

    answered = ParticipantQuestionAnswer.objects.filter(
        participant=_learnerstate.participant
    ).distinct().values_list('question')
    questions = TestingQuestion.objects.filter(
        module__in=_learnerstate.participant.classs.course.modules.all(),
        module__is_active=True,
    ).exclude(id__in=answered)

    if not questions:
        return redirect("learn.home")

    request.session["state"]["next_tasks_today"] = \
        ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).distinct('participant', 'question').count() + 1

    if _learnerstate.active_question:
        question_id = _learnerstate.active_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    def get():
        request.session["state"]["discussion_page_max"] = \
            Discussion.objects.filter(
                course=_participant.classs.course,
                question=_learnerstate.active_question,
                moderated=True,
                response=None
            ).count()

        request.session["state"]["discussion_page"] = \
            min(2, request.session["state"]["discussion_page_max"])

        index = request.session["state"]["discussion_page"]
        _messages = Discussion.objects.filter(
            course=_participant.classs.course,
            question=_learnerstate.active_question,
            moderated=True,
            response=None
        ).order_by("publishdate").reverse()[:index]

        state["total_tasks_today"] = _learnerstate.get_total_questions()
        if state['next_tasks_today'] > state["total_tasks_today"]:
            return redirect("learn.home")

        return render(request, "learn/next.html", {
            "state": state,
            "user": user,
            "question": _learnerstate.active_question,
            "messages": _messages,
        })

    def update_num_question_metric():
        update_metric(
            "total.questions",
            1,
            metric_type="SUM"
        )

    def update_perc_correct_answers(name, days_ago):
        date_range = (
            datetime.now().date() - timedelta(days=days_ago),
            datetime.now(),
        )
        total = ParticipantQuestionAnswer.objects.filter(
            answerdate__range=date_range
        ).count()
        if total > 0:
            value = ParticipantQuestionAnswer.objects.filter(
                answerdate__range=date_range,
                correct=True
            ).count() / total
        else:
            value = 0
        update_metric(
            "questions.correct." + name,
            value * 100,
            "LAST"
        )

    def update_all_perc_correct_answers():
        # Update metrics
        update_perc_correct_answers('24hr', 1)
        update_perc_correct_answers('48hr', 2)
        update_perc_correct_answers('7days', 7)
        update_perc_correct_answers('32days', 32)

    def post():
        request.session["state"]["discussion_comment"] = False
        request.session["state"]["discussion_responded_id"] = None
        request.session["state"]["report_sent"] = False

        # answer provided
        if "answer" in request.POST.keys():
            _ans_id = request.POST["answer"]

            options = _learnerstate.active_question.testingquestionoption_set
            try:
                _option = options.get(pk=_ans_id)
            except TestingQuestionOption.DoesNotExist:
                return redirect("learn.next")

            _learnerstate.active_result = _option.correct
            _learnerstate.save()

            # Answer question
            _participant.answer(_option.question, _option)

            # Update metrics
            update_num_question_metric()
            update_all_perc_correct_answers()

            # Check for awards
            if _option.correct:

                # Important
                _total_correct = ParticipantQuestionAnswer.objects.filter(
                    participant=_participant,
                    correct=True
                ).count()
                if _total_correct == 1:
                    _participant.award_scenario(
                        "1_CORRECT",
                        _learnerstate.active_question.module
                    )

                elif _total_correct == 15:
                    _participant.award_scenario(
                        "15_CORRECT",
                        _learnerstate.active_question.module
                    )

                elif _total_correct == 30:
                    _participant.award_scenario(
                        "30_CORRECT",
                        _learnerstate.active_question.module
                    )

                elif _total_correct == 100:
                    _participant.award_scenario(
                        "100_CORRECT",
                        _learnerstate.active_question.module
                    )

                last_3 = ParticipantQuestionAnswer.objects.filter(
                    participant=_participant
                ).order_by("answerdate").reverse()[:3]

                if last_3.count() == 3 \
                        and len([i for i in last_3 if i.correct]) == 3:
                    _participant.award_scenario(
                        "3_CORRECT_RUNNING",
                        _learnerstate.active_question.module
                    )

                last_5 = ParticipantQuestionAnswer.objects.filter(
                    participant=_participant
                ).order_by("answerdate").reverse()[:5]

                if last_5.count() == 5 \
                        and len([i for i in last_5 if i.correct]) == 5:
                    _participant.award_scenario(
                        "5_CORRECT_RUNNING",
                        _learnerstate.active_question.module
                    )

                return redirect("learn.right")

            else:
                return redirect("learn.wrong")

        # new comment created
        elif "comment" in request.POST.keys() \
                and request.POST["comment"] != "":
            _usr = Learner.objects.get(pk=user["id"])
            _comment = request.POST["comment"]
            _message = Discussion(
                course=_participant.classs.course,
                question=_learnerstate.active_question,
                response=None,
                content=_comment, author=_usr, publishdate=datetime.now()
            )
            _message.save()
            request.session["state"]["discussion_comment"] = True
            request.session["state"]["discussion_response_id"] = None

        elif "reply" in request.POST.keys() and request.POST["reply"] != "":
            _usr = Learner.objects.get(pk=user["id"])
            _comment = request.POST["reply"]
            _parent = Discussion.objects.get(pk=request.POST["reply_button"])
            _message = Discussion(
                course=_participant.classs.course,
                question=_learnerstate.active_question,
                response=_parent,
                content=_comment, author=_usr, publishdate=datetime.now())
            _message.save()
            request.session["state"]["discussion_responded_id"] \
                = request.session["state"]["discussion_response_id"]
            request.session["state"]["discussion_response_id"] = None

        # show more comments
        elif "page" in request.POST.keys():
            request.session["state"]["discussion_page"] += 2
            if request.session["state"]["discussion_page"] \
                    > request.session["state"]["discussion_page_max"]:
                request.session["state"]["discussion_page"] \
                    = request.session["state"]["discussion_page_max"]
            request.session["state"]["discussion_response_id"] = None

        # show reply to comment comment
        elif "comment_response_button" in request.POST.keys():
            request.session["state"]["discussion_response_id"] \
                = request.POST["comment_response_button"]

        _messages = \
            Discussion.objects.filter(
                course=_participant.classs.course,
                question=_learnerstate.active_question,
                moderated=True,
                response=None
            ).order_by("publishdate")\
            .reverse()[:request.session["state"]["discussion_page"]]

        state["total_tasks_today"] = _learnerstate.get_total_questions()

        return render(
            request,
            "learn/next.html",
            {
                "state": state,
                "user": user,
                "question": _learnerstate.active_question,
                "messages": _messages,
            }
        )

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def adminpreview(request, questionid):
    def get():
        question = TestingQuestion.objects.get(id=questionid)
        if "state" not in request.session.keys():
            request.session["state"] = {}
        request.session["state"]["next_tasks_today"] = 1
        request.session["state"]["discussion_page_max"] = \
            Discussion.objects.filter(
                question=question,
                moderated=True,
                response=None
            ).count()

        request.session["state"]["discussion_page"] = \
            min(2, request.session["state"]["discussion_page_max"])

        index = request.session["state"]["discussion_page"]

        messages = Discussion.objects.filter(
            question=question,
            moderated=True,
            response=None
        ).order_by("publishdate").reverse()[:index]

        return render(request, "learn/next.html", {
            "question": question,
            "messages": messages,
            "preview": True
        })

    def post():
        request.session["state"]["discussion_comment"] = False
        request.session["state"]["discussion_responded_id"] = None
        question = TestingQuestion.objects.get(id=questionid)
        # answer provided
        if "answer" in request.POST.keys():
            ans_id = request.POST["answer"]
            option = question.testingquestionoption_set.get(pk=ans_id)

            # Check for awards
            if option.correct:
                return HttpResponseRedirect("right/%s" % questionid)

            else:
                return HttpResponseRedirect("wrong/%s" % questionid)

        request.session["state"]["next_tasks_today"] = 1
        request.session["state"]["discussion_page_max"] = \
            Discussion.objects.filter(
                question=question,
                moderated=True,
                response=None
            ).count()

        request.session["state"]["discussion_page"] = \
            min(2, request.session["state"]["discussion_page_max"])

        index = request.session["state"]["discussion_page"]
        messages = Discussion.objects.filter(
            question=question,
            moderated=True,
            response=None
        ).order_by("publishdate").reverse()[:index]

        return render(request, "learn/next.html", {
            "question": question,
            "messages": messages,
            "preview": True
        })

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def adminpreview_right(request, questionid):
    def get():
        question = TestingQuestion.objects.get(id=questionid)
        if "state" not in request.session.keys():
            request.session["state"] = {}
        request.session["state"]["next_tasks_today"] = 1
        request.session["state"]["discussion_page_max"] = \
            Discussion.objects.filter(
                question=question,
                moderated=True,
                response=None
            ).count()

        # Discussion page?
        request.session["state"]["discussion_page"] = \
            min(2, request.session["state"]["discussion_page_max"])

        # Messages for discussion page
        messages = \
            Discussion.objects.filter(
                question=question,
                moderated=True,
                response=None
            ).order_by("publishdate")\
            .reverse()[:request.session["state"]["discussion_page"]]

        return render(
            request,
            "learn/right.html",
            {
                "question": question,
                "messages": messages,
                "points": 1
            }
        )

    return resolve_http_method(request, [get])


@user_passes_test(lambda u: u.is_staff)
def adminpreview_wrong(request, questionid):
    def get():
        question = TestingQuestion.objects.get(id=questionid)
        if "state" not in request.session.keys():
            request.session["state"] = {}
        request.session["state"]["next_tasks_today"] = 1
        request.session["state"]["discussion_page_max"] = \
            Discussion.objects.filter(
                question=question,
                moderated=True,
                response=None
            ).count()

        # Discussion page?
        request.session["state"]["discussion_page"] = \
            min(2, request.session["state"]["discussion_page_max"])

        # Messages for discussion page
        messages = \
            Discussion.objects.filter(
                question=question,
                moderated=True,
                response=None
            ).order_by("publishdate")\
            .reverse()[:request.session["state"]["discussion_page"]]

        return render(
            request,
            "learn/wrong.html",
            {
                "question": question,
                "messages": messages,
            }
        )

    return resolve_http_method(request, [get])


def get_badge_awarded(participant):
    # Get relevant badge related to scenario
    badgepoints = None
    badge = ParticipantBadgeTemplateRel.objects.filter(
        participant=participant,
        awarddate__range=[
            datetime.today()-timedelta(seconds=2),
            datetime.today()
        ]
    ).order_by('-awarddate').first()

    if badge:
        badgetemplate = badge.badgetemplate
        badgepoints = GamificationScenario.objects.get(
            badge__id=badgetemplate.id
        ).point
    else:
        badgetemplate = None

    return badgetemplate, badgepoints,


def get_points_awarded(participant):
    # Get current participant question answer
    answer = ParticipantQuestionAnswer.objects.filter(
        participant=participant,
    ).latest('answerdate')

    # Get question
    question = answer.question

    # Get points
    if question.points is 0:
        question.points = 1
        question.save()

    return question.points


# Right Answer Screen
@oneplus_state_required
@oneplus_login_required
def right(request, state, user):

    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()
    request.session["state"]["right_tasks_today"] = \
        ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).distinct('participant', 'question').count()
    state["total_tasks_today"] = _learnerstate.get_total_questions()
    if _learnerstate.active_question:
        question_id = _learnerstate.active_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    def get():
        if _learnerstate.active_result:
            # Max discussion page
            request.session["state"]["discussion_page_max"] = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    response=None
                ).count()

            # Discussion page?
            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            # Messages for discussion page
            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    response=None
                ).order_by("publishdate")\
                .reverse()[:request.session["state"]["discussion_page"]]

            # Get badge points
            badge, badge_points = get_badge_awarded(_participant)
            points = get_points_awarded(_participant)

            return render(
                request,
                "learn/right.html",
                {
                    "state": state,
                    "user": user,
                    "question": _learnerstate.active_question,
                    "messages": _messages,
                    "badge": badge,
                    "points": points,
                }
            )
        else:
            return HttpResponseRedirect("wrong")

    def post():
        if _learnerstate.active_result:
            request.session["state"]["discussion_comment"] = False
            request.session["state"]["discussion_responded_id"] = None
            request.session["state"]["report_sent"] = False

            # new comment created
            if "comment" in request.POST.keys()\
                    and request.POST["comment"] != "":
                _usr = Learner.objects.get(pk=user["id"])
                _comment = request.POST["comment"]
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    response=None,
                    content=_comment, author=_usr, publishdate=datetime.now())
                _message.save()
                request.session["state"]["discussion_comment"] = True
                request.session["state"]["discussion_response_id"] = None

            elif "reply" in request.POST.keys() \
                    and request.POST["reply"] != "":
                _usr = Learner.objects.get(pk=user["id"])
                _comment = request.POST["reply"]
                _parent = Discussion.objects.get(
                    pk=request.POST["reply_button"]
                )
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    response=_parent,
                    content=_comment, author=_usr,
                    publishdate=datetime.now()
                )
                _message.save()
                request.session["state"]["discussion_responded_id"] \
                    = request.session["state"]["discussion_response_id"]
                request.session["state"]["discussion_response_id"] = None

            # show more comments
            elif "page" in request.POST.keys():
                request.session["state"]["discussion_page"] += 2
                if request.session["state"]["discussion_page"]\
                        > request.session["state"]["discussion_page_max"]:
                    request.session["state"]["discussion_page"]\
                        = request.session["state"]["discussion_page_max"]
                request.session["state"]["discussion_response_id"] = None

            # show reply to comment comment
            elif "comment_response_button" in request.POST.keys():
                request.session["state"]["discussion_response_id"]\
                    = request.POST["comment_response_button"]

            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    response=None
                ).order_by("publishdate")\
                .reverse()[:request.session["state"]["discussion_page"]]

            return render(
                request,
                "learn/right.html",
                {
                    "state": state,
                    "user": user,
                    "question": _learnerstate.active_question,
                    "messages": _messages,
                }
            )
        else:
            return HttpResponseRedirect("wrong")

    return resolve_http_method(request, [get, post])


# Wrong Answer Screen
@oneplus_state_required
@oneplus_login_required
def wrong(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()
    request.session["state"]["wrong_tasks_today"] = \
        ParticipantQuestionAnswer.objects.filter(
            participant=_participant,
            answerdate__gte=date.today()
        ).distinct('participant', 'question').count()
    state["total_tasks_today"] = _learnerstate.get_total_questions()

    if _learnerstate.active_question:
        question_id = _learnerstate.active_question.id
        request.session["state"]["question_id"] = "<!-- TPS Version 4.3." \
                                                  + str(question_id) + "-->"

    def get():
        if not _learnerstate.active_result:
            request.session["state"]["discussion_page_max"] = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    response=None
                ).count()

            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    response=None
                ).order_by("publishdate")\
                .reverse()[:request.session["state"]["discussion_page"]]

            return render(
                request,
                "learn/wrong.html",
                {"state": state,
                 "user": user,
                 "question": _learnerstate.active_question,
                 "messages": _messages
                 }
            )
        else:
            return HttpResponseRedirect("right")

    def post():
        if not _learnerstate.active_result:
            request.session["state"]["discussion_comment"] = False
            request.session["state"]["discussion_responded_id"] = None
            request.session["state"]["report_sent"] = False

            # new comment created
            if "comment" in request.POST.keys() \
                    and request.POST["comment"] != "":
                _usr = Learner.objects.get(pk=user["id"])
                _comment = request.POST["comment"]
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    response=None,
                    content=_comment, author=_usr, publishdate=datetime.now())
                _message.save()
                request.session["state"]["discussion_comment"] = True
                request.session["state"]["discussion_response_id"] = None

            elif "reply" in request.POST.keys() \
                    and request.POST["reply"] != "":
                _usr = Learner.objects.get(pk=user["id"])
                _comment = request.POST["reply"]
                _parent = Discussion.objects.get(
                    pk=request.POST["reply_button"]
                )
                _message = Discussion(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    response=_parent,
                    content=_comment, author=_usr, publishdate=datetime.now()
                )
                _message.save()
                request.session["state"]["discussion_responded_id"] \
                    = request.session["state"]["discussion_response_id"]
                request.session["state"]["discussion_response_id"] = None

            # show more comments
            elif "page" in request.POST.keys():
                request.session["state"]["discussion_page"] += 2
                if request.session["state"]["discussion_page"] \
                        > request.session["state"]["discussion_page_max"]:
                    request.session["state"]["discussion_page"] \
                        = request.session["state"]["discussion_page_max"]
                request.session["state"]["discussion_response_id"] = None

            # show reply to comment comment
            elif "comment_response_button" in request.POST.keys():
                request.session["state"]["discussion_response_id"]\
                    = request.POST["comment_response_button"]

            return render(
                request,
                "learn/wrong.html",
                {
                    "state": state,
                    "user": user,
                    "question": _learnerstate.active_question
                }
            )
        else:
            return HttpResponseRedirect("right")

    return resolve_http_method(request, [get, post])


# Discuss Answer Screen
@oneplus_state_required
@oneplus_login_required
def discuss(request, state, user):
    def get():
        return render(request, "auth/discuss.html", {"state": state})

    def post():
        return render(request, "auth/discuss.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Inbox Screen
@oneplus_state_required
@oneplus_login_required
def inbox(request, state, user):
    # get inbox messages
    _participant = Participant.objects.get(pk=user["participant_id"])
    request.session["state"]["inbox_unread"] = Message.unread_message_count(
        _participant.learner,
        _participant.classs.course
    )

    def get():
        _messages = Message.get_messages(
            _participant.learner,
            _participant.classs.course, 20
        )
        return render(
            request,
            "com/inbox.html",
            {"state": state,
             "user": user,
             "messages": _messages,
             "message_count": len(_messages)}
        )

    def post():
        # hide message
        if "hide" in request.POST.keys() and request.POST["hide"] != "":
            _usr = Learner.objects.get(pk=user["id"])
            _msg = Message.objects.get(pk=request.POST["hide"])
            _msg.view_message(_usr)
            request.session["state"]["inbox_unread"] = Message.unread_message_count(
                _participant.learner,
                _participant.classs.course
            )
            _msg.hide_message(_usr)

        _messages = Message.get_messages(
            _participant.learner,
            _participant.classs.course,
            20
        )
        return render(
            request,
            "com/inbox.html",
            {
                "state": state,
                "user": user,
                "messages": _messages,
                "message_count": len(_messages)
            }
        )

    return resolve_http_method(request, [get, post])


# Inbox Detail Screen
@oneplus_state_required
@oneplus_login_required
def inbox_detail(request, state, user, messageid):
    # get inbox messages
    _participant = Participant.objects.get(pk=user["participant_id"])
    request.session["state"]["inbox_unread"] = Message.unread_message_count(
        _participant.learner, _participant.classs.course
    )
    _message = Message.objects.get(pk=messageid)
    _message.view_message(_participant.learner)

    def get():
        return render(
            request,
            "com/inbox_detail.html",
            {"state": state,
             "user": user,
             "message": _message}
        )

    def post():
        # hide message
        if "hide" in request.POST.keys():
            _message.hide_message(_participant.learner)
            return HttpResponseRedirect("/inbox")

        return render(
            request,
            "com/inbox_detail.html",
            {
                "state": state,
                "user": user,
                "message": _message
            }
        )

    return resolve_http_method(request, [get, post])


# Inbox Send Screen
@oneplus_state_required
@oneplus_login_required
def inbox_send(request, state, user):
    # get inbox messages
    _participant = Participant.objects.get(pk=user["participant_id"])
    request.session["state"]["inbox_sent"] = False

    def get():

        return render(request, "com/inbox_send.html", {"state": state,
                                                       "user": user})

    def post():
        # new message created
        if "comment" in request.POST.keys() and request.POST["comment"] != "":
            # Get comment
            _comment = request.POST["comment"]

            # Subject
            subject = ' '.join([
                _participant.learner.first_name,
                _participant.learner.last_name
            ])

            # Create and save message
            _message = Message(
                name=subject[:50],
                description=_comment[:50],
                course=_participant.classs.course,
                content=_comment,
                publishdate=datetime.now(),
                author=_participant.learner,
                direction=2
            )
            _message.save()

            try:
                # Send email to info@oneplus.co.za
                mail_managers(
                    subject=subject,
                    message=_comment,
                    fail_silently=False
                )
                # Set inbox send to true
                request.session["state"]["inbox_sent"] = True
            except Exception:
                request.session["state"]["inbox_sent"] = False

        return render(
            request,
            "com/inbox_send.html",
            {
                "state": state,
                "user": user
            }
        )

    return resolve_http_method(request, [get, post])


# Chat Groups Screen
@oneplus_state_required
@oneplus_login_required
def chatgroups(request, state, user):
    # get chat groups
    _groups = Participant.objects.get(
        pk=user["participant_id"]
    ).classs.course.chatgroup_set.all()

    for g in _groups:
        _last_msg = g.chatmessage_set.order_by("publishdate").reverse().first()
        if _last_msg is not None:
            g.last_message = _last_msg

    def get():
        return render(
            request,
            "com/chatgroup.html",
            {
                "state": state,
                "user": user,
                "groups": _groups
            }
        )

    def post():
        return render(request, "com/chatgroup.html", {"state": state,
                                                      "user": user,
                                                      "groups": _groups})

    return resolve_http_method(request, [get, post])


# Chat Screen
@oneplus_state_required
@oneplus_login_required
def chat(request, state, user, chatid):
    # get chat group
    _group = ChatGroup.objects.get(pk=chatid)
    request.session["state"]["chat_page_max"] = _group.chatmessage_set.count()

    def get():
        request.session["state"]["chat_page"] \
            = min(10, request.session["state"]["chat_page_max"])
        _messages = _group.chatmessage_set\
            .order_by("publishdate")\
            .reverse()[:request.session["state"]["chat_page"]]
        return render(request, "com/chat.html", {"state": state,
                                                 "user": user,
                                                 "group": _group,
                                                 "messages": _messages})

    def post():
        # new comment created
        if "comment" in request.POST.keys() and request.POST["comment"] != "":
            _usr = Learner.objects.get(pk=user["id"])
            _comment = request.POST["comment"]
            _message = ChatMessage(
                chatgroup=_group,
                content=_comment,
                author=_usr,
                publishdate=datetime.now()
            )
            _message.save()
            request.session["state"]["chat_page_max"] += 1

        # show more comments
        elif "page" in request.POST.keys():
            request.session["state"]["chat_page"] += 10
            if request.session["state"]["chat_page"] \
                    > request.session["state"]["chat_page_max"]:
                request.session["state"]["chat_page"]\
                    = request.session["state"]["chat_page_max"]

        _messages = _group.chatmessage_set.order_by("publishdate")\
            .reverse()[:request.session["state"]["chat_page"]]
        return render(
            request,
            "com/chat.html",
            {
                "state": state,
                "user": user,
                "group": _group,
                "messages": _messages
            }
        )

    return resolve_http_method(request, [get, post])


# Blog Hero Screen
@oneplus_state_required
@oneplus_login_required
def blog_hero(request, state, user):
    # get blog entry
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    request.session["state"]["blog_page_max"] = Post.objects.filter(
        course=_course
    ).count()
    _posts = Post.objects.filter(
        course=_course
    ).order_by("publishdate").reverse()[:4]
    request.session["state"]["blog_num"] = _posts.count()

    def get():
        return render(
            request,
            "com/bloghero.html",
            {
                "state": state,
                "user": user,
                "posts": _posts
            }
        )

    def post():
        return render(
            request,
            "com/bloghero.html",
            {
                "state": state,
                "user": user,
                "posts": _posts
            }
        )

    return resolve_http_method(request, [get, post])


# Blog List Screen
@oneplus_state_required
@oneplus_login_required
def blog_list(request, state, user):
    # get blog entry
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    request.session["state"]["blog_page_max"]\
        = Post.objects.filter(course=_course).count()

    def get():
        request.session["state"]["blog_page"] \
            = min(10, request.session["state"]["blog_page_max"])
        _posts = Post.objects.filter(course=_course)\
            .order_by("publishdate")\
            .reverse()[:request.session["state"]["blog_page"]]

        return render(request, "com/bloglist.html", {"state": state,
                                                     "user": user,
                                                     "posts": _posts})

    def post():
        # show more blogs
        if "page" in request.POST.keys():
            request.session["state"]["blog_page"] += 10
            if request.session["state"]["blog_page"] \
                    > request.session["state"]["blog_page_max"]:
                request.session["state"]["blog_page"] \
                    = request.session["state"]["blog_page_max"]

        _posts = Post.objects.filter(
            course=_course
        ).order_by("publishdate") \
            .reverse()[:request.session["state"]["blog_page"]]

        return render(
            request,
            "com/bloglist.html",
            {
                "state": state,
                "user": user,
                "posts": _posts
            }
        )

    return resolve_http_method(request, [get, post])


# Blog Screen
@oneplus_state_required
@oneplus_login_required
def blog(request, state, user, blogid):
    # get blog entry
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    _post = Post.objects.get(pk=blogid)
    _next = Post.objects.filter(
        course=_course,
        publishdate__gt=_post.publishdate
    ).exclude(id=_post.id).order_by("publishdate").first()
    _previous = Post.objects.filter(
        course=_course,
        publishdate__lt=_post.publishdate
    ).exclude(id=_post.id).order_by("publishdate").reverse().first()

    if _next is not None:
        state["blog_next"] = _next.id
    else:
        state["blog_next"] = None

    if _previous is not None:
        state["blog_previous"] = _previous.id
    else:
        state["blog_previous"] = None

    def get():
        return render(
            request,
            "com/blog.html",
            {"state": state,
             "user": user,
             "post": _post}
        )

    def post():
        return render(
            request,
            "com/blog.html",
            {
                "state": state,
                "user": user,
                "post": _post
            }
        )

    return resolve_http_method(request, [get, post])


# OnTrack Screen
@oneplus_state_required
@oneplus_login_required
def ontrack(request, state, user):
    # get on track state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    _modules = Participant.objects.get(
        pk=user["participant_id"]).classs.course.modules.all().order_by('order')

    # Calculate achieved score
    for m in _modules:
        _answers = _participant.participantquestionanswer_set.filter(
            question__module__id=m.id)
        if _answers.count() < 10:
            m.score = -1
        else:
            m.score = _answers.filter(
                correct=True
            ).count() / _answers.count() * 100

    def get():
        return render(
            request,
            "prog/ontrack.html",
            {
                "state": state,
                "user": user,
                "modules": _modules
            }
        )

    def post():
        return render(
            request,
            "prog/ontrack.html",
            {
                "state": state,
                "user": user,
                "modules": _modules
            }
        )

    return resolve_http_method(request, [get, post])


# Leaderboard Screen
@oneplus_state_required
@oneplus_login_required
def leader(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    request.session["state"]["leader_region"] = None

    def leader_position(location):

        return Participant.objects.filter(
            classs=_participant.classs,
            points__gt=_participant.points,
        ).count() + 1

    def get_leaderboard(location):
        return Participant.objects.filter(
            classs=_participant.classs,
        ).order_by("-points")[:10]

    def get():
        request.session["state"]["leader_menu"] = False

        # Get leaderboard and position
        _location = request.session["state"]["leader_region"]
        _learners = list(get_leaderboard(_location))
        request.session["state"]["leader_place"] = leader_position(_location)

        try:
            index = _learners.index(_participant)
            _learners[index].me = True
        finally:
            return render(
                request,
                "prog/leader.html",
                {
                    "state": state,
                    "user": user,
                    "learners": _learners
                }
            )

    def post():
        # show region menu?
        if "leader_menu" in request.POST:
            request.session["state"]["leader_menu"] \
                = request.POST["leader_menu"] != 'True'
        elif "region" in request.POST:
            request.session["state"]["leader_menu"] = False
            request.session["state"]["leader_region"] = request.POST["region"]

        # Get leaderboard and position
        _location = request.session["state"]["leader_region"]
        _learners = list(get_leaderboard(_location))
        request.session["state"]["leader_place"] = leader_position(_location)

        # Get unique regions
        request.session["state"]["leader_regions"] \
            = list([{"area": COUNTRYWIDE}]) \
            + list(Learner.objects.values("area").distinct().all())

        # Tag the user
        try:
            index = _learners.index(_participant)
            _learners[index].me = True
        finally:
            return render(
                request,
                "prog/leader.html",
                {
                    "state": state,
                    "user": user,
                    "learners": _learners
                }
            )

    return resolve_http_method(request, [get, post])


# Points Screen
@oneplus_state_required
@oneplus_login_required
def points(request, state, user):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _course = _participant.classs.course
    _modules = _participant.classs.course.modules.all().order_by('order')
    request.session["state"]["points_points"] = _participant.points

    def get_points_per_module():
        for m in _modules:
            answers = ParticipantQuestionAnswer.objects.filter(
                participant=_participant,
                question__module=m,
                correct=True
            )
            module_points = 0
            for answer in answers:
                module_points += answer.question.points

            m.score = module_points

    def get():
        get_points_per_module()
        return render(
            request,
            "prog/points.html",
            {
                "state": state,
                "user": user,
                "modules": _modules
            }
        )

    def post():
        get_points_per_module()
        return render(
            request,
            "prog/points.html",
            {
                "state": state,
                "user": user,
                "modules": _modules
            }
        )

    return resolve_http_method(request, [get, post])


# Badges Screen
@oneplus_state_required
@oneplus_login_required
def badges(request, state, user):
    # get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _course = _participant.classs.course
    _allscenarios = GamificationScenario.objects.exclude(badge__isnull=True)\
        .filter(course=_course).prefetch_related("badge").order_by('badge__order')
    _badges = [scenario.badge for scenario in _allscenarios]

    # Link achieved badges
    for x in _badges:
        if ParticipantBadgeTemplateRel.objects.filter(
                participant=_participant,
                badgetemplate=x
        ).exists():
            x.achieved = True

    def get():
        return render(request, "prog/badges.html", {
            "state": state,
            "user": user,
            "badges": _badges,
            "participant": _participant
        })

    def post():
        return render(
            request,
            "prog/badges.html",
            {
                "state": state,
                "user": user,
                "badges": _badges,
                "participant": _participant
            }
        )

    return resolve_http_method(request, [get, post])

# Menu Screen


@oneplus_state_required
@oneplus_login_required
def menu(request, state, user):
    def get():
        return render(
            request, "core/menu.html", {"state": state, "user": user})

    def post():
        return render(
            request, "core/menu.html", {"state": state, "user": user})

    return resolve_http_method(request, [get, post])

# About Screen


@oneplus_state_required
@oneplus_check_user
def about(request, state, user):
    def get():
        return render(
            request, "misc/about.html", {"state": state, "user": user})

    def post():
        return render(
            request, "misc/about.html", {"state": state, "user": user})

    return resolve_http_method(request, [get, post])


# Contact Screen
@oneplus_state_required
@oneplus_check_user
def contact(request, state, user):
    def get():
        state["sent"] = False
        state['fname'] = ""
        state['sname'] = ""
        state['comment'] = ""
        state['contact'] = ""
        state['school'] = ""
        state['valid_message'] = ""

        return render(
            request, "misc/contact.html", {"state": state, "user": user})

    def post():
        # Get message
        state['valid'] = True
        state['valid_message'] = ["Please complete the following fields:"]

        # Get contact details
        if "fname" in request.POST.keys() and len(request.POST["fname"]) >= 3:
            _fname = request.POST["fname"]
            state['fname'] = _fname
        else:
            state['valid'] = False
            state['valid_message'].append("First Name")

        if "sname" in request.POST.keys() and len(request.POST["sname"]) >= 3:
            _sname = request.POST["sname"]
            state['sname'] = _sname
        else:
            state['valid'] = False
            state['valid_message'].append("Last Name")

        if "contact" in request.POST.keys() and len(
                request.POST["contact"]) >= 3:
            _contact = request.POST["contact"]
            state['contact'] = _contact
        else:
            state['valid'] = False
            state['valid_message'].append("Mobile number or Email")

        if "comment" in request.POST.keys() and len(
                request.POST["comment"]) >= 3:
            _comment = request.POST["comment"]
            state['comment'] = _comment
        else:
            state['valid'] = False
            state['valid_message'].append("Message")

        if "school" in request.POST.keys():
            _school = request.POST["school"]
            state['school'] = _school

        if state['valid']:
            message = "\n".join([
                "First Name: " + _fname,
                "Last Name: " + _sname,
                "School: " + _school,
                "Contact: " + _contact,
                _comment,
            ])
            # Send email to info@oneplus.co.za
            mail_managers(
                subject='Contact Us Message - ' + _contact,
                message=message,
                fail_silently=False)

            state["sent"] = True

        return render(
            request, "misc/contact.html", {"state": state, "user": user})

    return resolve_http_method(request, [get, post])


#Report Question Screen
@oneplus_state_required
@oneplus_login_required
def report_question(request, state, user, questionid, frm):
    _participant = Participant.objects.get(pk=user["participant_id"])
    _learnerstate = LearnerState.objects.filter(
        participant=_participant
    ).first()

    try:
        _question = TestingQuestion.objects.get(id=questionid)
    except ObjectDoesNotExist:
        return redirect("learn.home")

    if frm not in ['next', 'right', 'wrong']:
        return redirect("learn.home")

    def get():
        return render(
            request, "learn/report_question.html",
            {
                "state": state,
                "user": user,
                "question_number": _question.order,
            }
        )

    def post():
        if "issue" in request.POST.keys() and request.POST["issue"] != "" and \
                "fix" in request.POST.keys() and request.POST["fix"] != "":
            _usr = Learner.objects.get(pk=user["id"])
            _issue = request.POST["issue"]
            _fix = request.POST["fix"]

            _report = Report(
                user=_usr,
                question=_question,
                issue=_issue,
                fix=_fix,
                response=None
            )

            _report.save()

            state["report_sent"] = True

            # if _learnerstate.active_result:
            #     # Max discussion page
            request.session["state"]["discussion_page_max"] = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    response=None
                ).count()

            # Discussion page?
            request.session["state"]["discussion_page"] = \
                min(2, request.session["state"]["discussion_page_max"])

            # Messages for discussion page
            _messages = \
                Discussion.objects.filter(
                    course=_participant.classs.course,
                    question=_learnerstate.active_question,
                    moderated=True,
                    response=None
                ).order_by("publishdate")\
                .reverse()[:request.session["state"]["discussion_page"]]

            return HttpResponseRedirect('/' + frm,
                                        {
                                            "state": state,
                                            "user": user,
                                            "question": _question,
                                            "messages": _messages,
                                        })
        else:
            return render(
                request, "learn/report_question.html",
                {
                    "state": state,
                    "user": user,
                    "question_number": _question.order,
                }
            )

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def dashboard_data(request):
    def get():

        from core.stats import (participants_registered_last_x_hours,
                                questions_answered_in_last_x_hours,
                                percentage_questions_answered_correctly_in_last_x_hours,
                                questions_answered_correctly_in_last_x_hours)
        from auth.stats import (learners_active_in_last_x_hours,
                                percentage_learner_sms_opt_ins,
                                percentage_learner_email_opt_ins,
                                number_learner_sms_opt_ins,
                                number_learner_email_opt_ins,
                                total_active_learners)

        response_data = {
            'num_learn_reg_24': participants_registered_last_x_hours(24),
            'num_learn_reg_48': participants_registered_last_x_hours(48),
            'num_learn_reg_168': participants_registered_last_x_hours(168),
            'num_learn_reg_744': participants_registered_last_x_hours(744),

            'num_learn_act_24': learners_active_in_last_x_hours(24),
            'num_learn_act_48': learners_active_in_last_x_hours(48),
            'num_learn_act_168': learners_active_in_last_x_hours(168),
            'num_learn_act_744': learners_active_in_last_x_hours(744),

            'num_q_ans_24': questions_answered_in_last_x_hours(24),
            'num_q_ans_48': questions_answered_in_last_x_hours(48),
            'num_q_ans_168': questions_answered_in_last_x_hours(168),
            'num_q_ans_744': questions_answered_in_last_x_hours(744),

            'num_q_ans_cor_24': questions_answered_correctly_in_last_x_hours(24),
            'num_q_ans_cor_48': questions_answered_correctly_in_last_x_hours(48),
            'num_q_ans_cor_168': questions_answered_correctly_in_last_x_hours(168),

            'prc_q_ans_cor_24': percentage_questions_answered_correctly_in_last_x_hours(24),
            'prc_q_ans_cor_48': percentage_questions_answered_correctly_in_last_x_hours(48),
            'prc_q_ans_cor_168': percentage_questions_answered_correctly_in_last_x_hours(168),

            'tot_learners': total_active_learners(),
            'num_sms_optin': number_learner_sms_opt_ins(),
            'num_email_optin': number_learner_email_opt_ins(),

            'prc_sms_optin': percentage_learner_sms_opt_ins(),
            'prc_email_optin': percentage_learner_email_opt_ins()
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def post():
        response_data = {
            'error': 'This is not the post office, get only'
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def dashboard(request):
    return render(
        request, "misc/dashboard.html",
        {
        }
    )


@user_passes_test(lambda u: u.is_staff)
def reports(request):
    return render(
        request, "misc/reports.html",
        {
        }
    )


@user_passes_test(lambda u: u.is_staff)
def reports_learner_unique_regions(request):
    data = CustomUser.objects.exclude(area__isnull=True).exclude(area__exact='').values('area').distinct()
    return HttpResponse(json.dumps(list(data)), content_type="application/json")


def report_learner_get_sql(qtype=1):
    # qtype: 1 - all
    #        2 - filtered by region
    sql = \
        'select cu.username, cu.first_name, cu.last_name, s.name, cu.area, ' \
        '    qt.cnt, ' \
        '    qc.cnt / ' \
        '    (case  ' \
        '        when qt.cnt is null then 1 ' \
        '        when qt.cnt = 0 then 1 ' \
        '        else qt.cnt ' \
        '    end)::numeric * 100 perc_corr ' \
        'from core_participant p ' \
        'inner join auth_customuser cu ' \
        '    on cu.id = p.learner_id ' \
        'inner join auth_learner l ' \
        '    on l.customuser_ptr_id = cu.id ' \
        'inner join organisation_school s ' \
        '    on s.id = l.school_id ' \
        'left join ( ' \
        '    select participant_id, count(correct) cnt ' \
        '    from core_participantquestionanswer ' \
        '    where correct = true ' \
        '    group by participant_id ' \
        '    ) qc ' \
        '    on qc.participant_id = p.id ' \
        'left join ( ' \
        '    select participant_id, count(1) cnt ' \
        '    from core_participantquestionanswer ' \
        '    group by participant_id ' \
        '    ) qt ' \
        '    on qt.participant_id = p.id '

    if qtype == 2:
        sql = sql + ' where cu.area = %s'

    return sql


@user_passes_test(lambda u: u.is_staff)
def report_learner(request, mode, region):
    if mode != '1' and mode != '2':
        return HttpResponseRedirect(reverse("reports.home"))

    headers = [('MSISDN', 'First Name', 'Last Name', 'School', 'Region', 'Questions Completed', 'Percentage Correct')]
    cursor = connection.cursor()
    file_name = 'learner_report'

    if region:
        sql = report_learner_get_sql(2)
        cursor.execute(sql, [region])
        file_name = '%s_%s' % (file_name, region)
    else:
        sql = report_learner_get_sql()
        cursor.execute(sql)

    data = cursor.fetchall()

    if mode == '1':
        return get_csv_report(data, file_name, headers)
    elif mode == '2':
        return get_xls_report(data, file_name, headers)


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
            if Course.objects.get(id=course):
                current_course = Course.objects.get(id=course)
                classes = Class.objects.all().filter(course=current_course)
            else:
                classes = None
        except ValueError, ObjectDoesNotExist:
            classes = None

    data = []
    for c in classes:
        line = {"id": c.id, "name": c.name}
        data.append(line)

    return HttpResponse(json.dumps(data), content_type="application/javascript")


def get_users(request, classs):
    if classs == 'all':
        participants = Participant.objects.all()
    else:
        try:
            classs = int(classs)

            if Class.objects.get(id=classs):
                current_class = Class.objects.get(id=classs)
                participants = Participant.objects.all().filter(classs=current_class)
        except ValueError, ObjectDoesNotExist:
            participants = None

    data = []
    for p in participants:
        line = {"id": p.learner.id, "name": p.learner.mobile}
        data.append(line)

    return HttpResponse(json.dumps(data), content_type="application/javascript")


@user_passes_test(lambda u: u.is_staff)
def report_response(request, report):
    db_report = Report.objects.filter(id=report).first()
    if db_report:
        db_participant = Participant.objects.filter(learner=db_report.user).first()

        if db_participant is None:
            return HttpResponse("Participant not found")
    else:
        return HttpResponse("Report %s not found" % report)

    def get():

        return render(
            request=request,
            template_name='misc/report_response.html',
            dictionary={'report': db_report, 'participant': db_participant}
        )

    def post():

        title_error = False
        dt_error = False
        content_error = False
        title = None
        date = None
        time = None
        content = None

        title_error, title = validate_title(request.POST)
        dt_error, date, time, dt = validate_publish_date_and_time(request.POST)
        content_error, content = validate_content(request.POST)

        if title_error or dt_error or content_error:
            return render(
                request=request,
                template_name='misc/report_response.html',
                dictionary={
                    'report': db_report,
                    'participant': db_participant,
                    'title_error': title_error,
                    'dt_error': dt_error,
                    'content_error': content_error,
                    'v_title': title,
                    'v_date': date,
                    'v_time': time,
                    'v_content': content
                }
            )
        else:
            db_report.create_response(title, content, dt)
            Message.objects.create(
                name=gen_username(request.user),
                description=title,
                course=db_participant.classs.course,
                content=content,
                publishdate=dt,
                author=request.user,
                direction=1,
            )
            return HttpResponseRedirect('/admin/communication/report')

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def message_response(request, msg):
    db_msg = Message.objects.filter(id=msg).first()

    if db_msg:
        db_participant = Participant.objects.filter(learner=db_msg.author).first()

        if db_participant is None:
            return HttpResponse("Participant not found")
    else:
        return HttpResponse("Message %s not found" % msg)

    def get():

        return render(
            request=request,
            template_name='misc/message_response.html',
            dictionary={'msg': db_msg, 'participant': db_participant}
        )

    def post():

        title_error = False
        dt_error = False
        content_error = False
        title = None
        date = None
        time = None
        content = None

        title_error, title = validate_title(request.POST)
        dt_error, date, time, dt = validate_publish_date_and_time(request.POST)
        content_error, content = validate_content(request.POST)

        if title_error or dt_error or content_error:
            return render(
                request=request,
                template_name='misc/message_response.html',
                dictionary={
                    'msg': db_msg,
                    'participant': db_participant,
                    'title_error': title_error,
                    'dt_error': dt_error,
                    'content_error': content_error,
                    'v_title': title,
                    'v_date': date,
                    'v_time': time,
                    'v_content': content
                }
            )
        else:
            Message.objects.create(
                name=gen_username(request.user),
                description=title,
                course=db_participant.classs.course,
                content=content,
                publishdate=dt,
                author=request.user,
                direction=1,
            )

            db_msg.responded = True
            db_msg.responddate = datetime.now()
            db_msg.save()

            return HttpResponseRedirect('/admin/communication/message/')

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def add_message(request):
    def get():
        return render(
            request=request,
            template_name='misc/message.html',
        )

    def post():
        name_error = False
        course_error = False
        class_error = False
        users_error = False
        direction_error = False
        dt_error = False
        content_error = False
        name = None
        course = None
        classs = None
        users = None
        direction = None
        date = None
        time = None
        content = None

        name_error, name = validate_name(request.POST)
        course_error, course = validate_to_course(request.POST)
        class_error, classs = validate_to_class(request.POST)
        users_error, users = validate_users(request.POST)
        direction_error, direction = validate_direction(request.POST)
        dt_error, date, time, dt = validate_publish_date_and_time(request.POST)
        content_error, content = validate_content(request.POST)

        if name_error or course_error or class_error or users_error or direction_error or dt_error or content_error:
            return render(
                request=request,
                template_name='misc/message.html',
                dictionary={
                    'name_error': name_error,
                    'to_course_error': course_error,
                    'to_class_error': class_error,
                    'direction_error': direction_error,
                    'dt_error': dt_error,
                    'content_error': content_error,
                    'v_name': name,
                    'v_direction': direction,
                    'v_date': date,
                    'v_time': time,
                    'v_content': content
                }
            )

        else:
            if course == "all":
                all_courses = Course.objects.all()

                for _course in all_courses:
                    all_classes = Class.objects.filter(course=_course)

                    for _classs in all_classes:
                        all_users = Participant.objects.filter(classs=_classs)

                        for u in all_users:
                            create_message(name, _course, _classs, direction, dt, content)
            else:
                course_obj = Course.objects.get(id=course)

                if classs == "all":
                    all_classes = Class.objects.filter(course=course_obj)

                    for c in all_classes:
                        all_users = Participant.objects.filter(classs=c)

                        for u in all_users:
                            create_message(name, course_obj, c, direction, dt, content)
                else:
                    classs_obj = Class.objects.get(id=classs)

                    if users == "all":
                        all_users = Participant.objects.filter(classs=classs_obj)

                        for u in all_users:
                            create_message(name, course_obj, classs_obj, direction, dt, content)
                    else:
                        learner = Learner.objects.get(id=users)
                        user = Participant.objects.filter(learner=learner).first()
                        create_message(name, course_obj, classs_obj, direction, dt, content)

        return HttpResponseRedirect('/admin/communication/message/')

    def create_message(name, course, classs, direction, publishdate, content):
        Message.objects.create(
            name=name,
            to_course=course,
            to_class=classs,
            content=content,
            publishdate=publishdate,
            author=request.user,
            direction=direction,
        )

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def view_message(request, msg):
    db_msg = Message.objects.filter(id=msg).first()

    if db_msg is None:
        return HttpResponse("Message not found")

    def get():
        return render(
            request=request,
            template_name='misc/message.html',
            dictionary={
                'message': db_msg,
                'ro': True
            }
        )

    def post():
        return render(
            request=request,
            template_name='misc/message.html',
            dictionary={
                'message': db_msg,
                'ro': True
            }
        )

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def discussion_response(request, disc):
    db_disc = Discussion.objects.filter(id=disc).first()

    if db_disc:
        db_participant = Participant.objects.filter(learner=db_disc.author).first()

        if db_participant is None:
            return HttpResponse("Participant not found")
    else:
        return HttpResponse("Discussion %s not found" % disc)

    def get():

        return render(
            request=request,
            template_name='misc/discussion_response.html',
            dictionary={'disc': db_disc, 'participant': db_participant}
        )

    def post():

        title_error = False
        dt_error = False
        content_error = False
        title = None

        title_error, title = validate_title(request.POST)
        dt_error, date, time, dt = validate_publish_date_and_time(request.POST)
        content_error, content = validate_content(request.POST)

        if title_error or dt_error or content_error:
            return render(
                request=request,
                template_name='misc/discussion_response.html',
                dictionary={
                    'disc': db_disc,
                    'participant': db_participant,
                    'title_error': title_error,
                    'dt_error': dt_error,
                    'content_error': content_error,
                    'v_title': title,
                    'v_date': date,
                    'v_time': time,
                    'v_content': content
                }
            )
        else:
            disc = Discussion.objects.create(
                name=gen_username(request.user),
                description=title,
                content=content,
                author=request.user,
                publishdate=dt,
                moderated=True,
                course=db_disc.course,
                module=db_disc.module,
                question=db_disc.question
            )

            db_disc.response = disc
            db_disc.save()

            return HttpResponseRedirect('/admin/communication/discussion/')

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def sms_response(request, sms):
    db_sms = Sms.objects.filter(id=sms).first()

    if db_sms:
        db_participant = Participant.objects.filter(learner__mobile__contains=db_sms.msisdn).first()

    else:
        return HttpResponse("Sms %s not found" % sms)

    def get():

        return render(
            request=request,
            template_name='misc/sms_response.html',
            dictionary={'sms': db_sms, 'participant': db_participant}
        )

    def post():

        dt_error = False
        content_error = False
        title = None
        date = None
        time = None
        content = None

        dt_error, date, time, dt = validate_publish_date_and_time(request.POST)
        content_error, content = validate_content(request.POST)

        if dt_error or content_error:
            return render(
                request=request,
                template_name='misc/sms_response.html',
                dictionary={
                    'sms': db_sms,
                    'participant': db_participant,
                    'dt_error': dt_error,
                    'content_error': content_error,
                    'v_date': date,
                    'v_time': time,
                    'v_content': content
                }
            )
        else:
            qsms = SmsQueue.objects.create(
                message=content,
                send_date=dt,
                msisdn=db_sms.msisdn
            )

            db_sms.responded = True
            db_sms.respond_date = datetime.now()
            db_sms.response = qsms
            db_sms.save()

            return HttpResponseRedirect('/admin/communication/sms/')

    return resolve_http_method(request, [get, post])