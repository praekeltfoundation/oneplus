from django.shortcuts import render, get_object_or_404, HttpResponse
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.contrib.auth import models
from django.contrib.auth import authenticate, login
from django.core.exceptions import ObjectDoesNotExist
from forms import *
from gamification.models import *
from communication.models import *
from organisation.models import *
from core.models import *
from oneplus.models import *
from datetime import *


# Code decorator to ensure that the user is logged in
def oneplus_login_required(f):
    def wrap(request, *args, **kwargs):
        if "user" not in request.session.keys():
            return HttpResponseRedirect("login")
        return f(request, user=request.session["user"], *args, **kwargs)
    wrap.__doc__=f.__doc__
    wrap.__name__=f.__name__
    return wrap


# Code decorator to ensure that view state exists and is properly handled
def oneplus_state_required(f):
    def wrap(request, *args, **kwargs):
        #Initialise the oneplus state
        #request.session.flush()
        request.session.set_expiry(0) # If value is 0, the user's session cookie will expire when the user's Web browser is closed.
        if "state" not in request.session.keys():
            request.session["state"] = {"menu_visible": False}

        #Manage menu state
        if request.method == "POST" and "switchmenu" in request.POST:
            request.session["state"]["menu_visible"] = request.POST["switchmenu"] != 'True'
        else:
            request.session["state"]["menu_visible"] = False

        return f(request, state=request.session["state"], *args, **kwargs)
    wrap.__doc__=f.__doc__
    wrap.__name__=f.__name__
    return wrap


# Action resolver to elegantly handle verbs in the views
def resolve_http_method(request, methods):
    if isinstance(methods, list):
        methods = { func.__name__.lower() : func for func in methods }
    if request.method.lower() not in methods.keys():
        return HttpResponse(status=501)
    return methods[request.method.lower()]()


# Login Screen
@oneplus_state_required
def login(request, state):
    def get():
        return render(request, "auth/login.html", {"state": state,
                                                   "form": LoginForm()})

    def post():
        form = LoginForm(request.POST)
        if form.is_valid():
            # Check if this is a registered user
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            if user is not None and user.is_active:
                try:
                    # Check that the user is a learner
                    _learner = user.learner

                    # Check which OnePlus course learner is on
                    _registered = None
                    for _parti in Participant.objects.filter(learner=_learner):
                        if _parti.classs.course.name == "One Plus Grade 11":
                            _registered = _parti

                    if _parti is not None:
                        request.session["user"] = {}
                        request.session["user"]["id"] = _learner.id
                        request.session["user"]["name"] = _learner.first_name
                        request.session["user"]["participant_id"] = _registered.id
                        request.session["user"]["points"] = _registered.points
                        request.session["user"]["place"] = 0  # TODO
                        request.session["user"]["badges"] = _registered.badgetemplate.count()
                        request.session["user"]["latest"] = _registered.badgetemplate.last().name

                        #login(request, user)
                        return HttpResponseRedirect("home")
                    else:
                        return HttpResponseRedirect("getconnected")
                except ObjectDoesNotExist:
                        return HttpResponseRedirect("getconnected")
            else:
                return HttpResponseRedirect("getconnected")
        else:
            return get()

    return resolve_http_method(request, [get, post])


# SMS Password Screen
@oneplus_state_required
def smspassword(request, state):
    def get():
        return render(request, "auth/smspassword.html", {"state": state})

    def post():
        return render(request, "auth/smspassword.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Get Connected Screen
@oneplus_state_required
def getconnected(request, state):
    def get():
        return render(request, "auth/getconnected.html", {"state": state})

    def post():
        return render(request, "auth/getconnected.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Welcome Screen
@oneplus_state_required
def welcome(request, state):
    def get():
        return render(request, "misc/welcome.html", {"state": state})

    def post():
        return render(request, "misc/welcome.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Home Screen
@oneplus_state_required
@oneplus_login_required
def home(request, state, user):
    def get():
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
    #get learner state
    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()
    if _learnerstate is None:
        _learnerstate = LearnerState(participant=Participant.objects.get(pk=user["participant_id"]))

    # check if new question required then show question
    _learnerstate.getnextquestion()

    def get():
        return render(request, "learn/next.html", {"state": state,
                                                   "user": user,
                                                   "question": _learnerstate.active_question})

    def post():
        # answer provided
        if "answer" in request.POST.keys():
            _ans_id = request.POST["answer"]
            _option = _learnerstate.active_question.testingquestionoption_set.get(pk=_ans_id)

            _answer = ParticipantQuestionAnswer(participant=Participant.objects.get(pk=user["participant_id"]), question=_learnerstate.active_question, option_selected=_option, correct=_option.correct, answerdate=datetime.now())
            _answer.save()

            _learnerstate.active_result = _option.correct
            _learnerstate.save()

            if _option.correct:
                return HttpResponseRedirect("right")
            else:
                return HttpResponseRedirect("wrong")
        else:
            return get()
    return resolve_http_method(request, [get, post])


# Right Answer Screen
@oneplus_state_required
@oneplus_login_required
def right(request, state, user):
    #get learner state
    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

    def get():
        if _learnerstate.active_result:
            return render(request, "learn/right.html", {"state": state,
                                                        "user": user,
                                                        "question": _learnerstate.active_question})
        else:
            return HttpResponseRedirect("wrong")

    def post():
        if _learnerstate.active_result:
            return render(request, "learn/right.html", {"state": state,
                                                        "user": user,
                                                        "question": _learnerstate.active_question})
        else:
            return HttpResponseRedirect("wrong")

    return resolve_http_method(request, [get, post])


# Wrong Answer Screen
@oneplus_state_required
@oneplus_login_required
def wrong(request, state, user):
    #get learner state
    _learnerstate = LearnerState.objects.filter(participant__id=user["participant_id"]).first()

    def get():
        if not _learnerstate.active_result:
            return render(request, "learn/wrong.html", {"state": state,
                                                        "user": user,
                                                        "question": _learnerstate.active_question})
        else:
            return HttpResponseRedirect("right")

    def post():
        if not _learnerstate.active_result:
            return render(request, "learn/wrong.html", {"state": state,
                                                        "user": user,
                                                        "question": _learnerstate.active_question})
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
    #get inbox messages
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    _messages = Message.objects.filter(course=_course, direction=1).order_by("publishdate").reverse()[:20]

    def get():
        return render(request, "com/inbox.html", {"state": state,
                                                  "user": user,
                                                  "messages": _messages,
                                                  "message_count":_messages.count()})

    def post():
        return render(request, "com/inbox.html", {"state": state,
                                                  "user": user,
                                                  "messages": _messages,
                                                  "message_count":_messages.count()})

    return resolve_http_method(request, [get, post])


# Chat Groups Screen
@oneplus_state_required
@oneplus_login_required
def chatgroups(request, state, user):
    #get chat groups
    _groups = Participant.objects.get(pk=user["participant_id"]).classs.course.chatgroup_set.all()

    for g in _groups:
        _last_msg = g.chatmessage_set.order_by("publishdate").reverse().first()
        if _last_msg is not None:
            g.last_message = _last_msg

    def get():
        return render(request, "com/chatgroup.html", {"state": state,
                                                      "user": user,
                                                      "groups": _groups})

    def post():
        return render(request, "com/chatgroup.html", {"state": state,
                                                      "user": user,
                                                      "groups": _groups})

    return resolve_http_method(request, [get, post])


# Chat Screen
@oneplus_state_required
@oneplus_login_required
def chat(request, state, user, chatid):
    #get chat group
    _group = ChatGroup.objects.get(pk=chatid)
    request.session["state"]["chat_page_max"] = _group.chatmessage_set.count()

    def get():
        request.session["state"]["chat_page"] = min(10, request.session["state"]["chat_page_max"])
        _messages = _group.chatmessage_set.order_by("publishdate").reverse()[:request.session["state"]["chat_page"]]
        return render(request, "com/chat.html", {"state": state,
                                                 "user": user,
                                                 "group": _group,
                                                 "messages": _messages})

    def post():
        #new comment created
        if "comment" in request.POST.keys() and request.POST["comment"] != "":
            _usr = Learner.objects.get(pk=user["id"])
            _comment = request.POST["comment"]
            _message = ChatMessage(chatgroup=_group, content=_comment, author=_usr, publishdate=datetime.now())
            _message.save()
            request.session["state"]["chat_page_max"] += 1

        #show more comments
        elif "page" in request.POST.keys():
            request.session["state"]["chat_page"] += 10
            if request.session["state"]["chat_page"] > request.session["state"]["chat_page_max"]:
                request.session["state"]["chat_page"] = request.session["state"]["chat_page_max"]

        _messages = _group.chatmessage_set.order_by("publishdate").reverse()[:request.session["state"]["chat_page"]]
        return render(request, "com/chat.html", {"state": state,
                                                 "user": user,
                                                 "group": _group,
                                                 "messages": _messages})

    return resolve_http_method(request, [get, post])


# Blog Hero Screen
@oneplus_state_required
@oneplus_login_required
def blog_hero(request, state, user):
    #get blog entry
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    request.session["state"]["blog_page_max"] = Post.objects.filter(course=_course).count()
    _posts = Post.objects.filter(course=_course).order_by("publishdate").reverse()[:4]
    request.session["state"]["blog_num"] = _posts.count()

    def get():
        return render(request, "com/bloghero.html", {"state": state,
                                                     "user": user,
                                                     "posts": _posts})

    def post():
        return render(request, "com/bloghero.html", {"state": state,
                                                     "user": user,
                                                     "posts": _posts})

    return resolve_http_method(request, [get, post])


# Blog List Screen
@oneplus_state_required
@oneplus_login_required
def blog_list(request, state, user):
    #get blog entry
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    request.session["state"]["blog_page_max"] = Post.objects.filter(course=_course).count()

    def get():
        request.session["state"]["blog_page"] = min(10, request.session["state"]["blog_page_max"])
        _posts = Post.objects.filter(course=_course).order_by("publishdate").reverse()[:request.session["state"]["blog_page"]]
        return render(request, "com/bloglist.html", {"state": state,
                                                     "user": user,
                                                     "posts": _posts})

    def post():
        #show more blogs
        if "page" in request.POST.keys():
            request.session["state"]["blog_page"] += 10
            if request.session["state"]["blog_page"] > request.session["state"]["blog_page_max"]:
                request.session["state"]["blog_page"] = request.session["state"]["blog_page_max"]

        _posts = Post.objects.filter(course=_course).order_by("publishdate").reverse()[:request.session["state"]["blog_page"]]
        return render(request, "com/bloglist.html", {"state": state,
                                                     "user": user,
                                                     "posts": _posts})

    return resolve_http_method(request, [get, post])


# Blog Screen
@oneplus_state_required
@oneplus_login_required
def blog(request, state, user, blogid):
    #get blog entry
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    _posts = Post.objects.filter(course=_course).order_by("publishdate").reverse()

    _post = Post.objects.get(pk=blogid)
    _next = Post.objects.filter(course=_course, publishdate__gt=_post.publishdate).exclude(id=_post.id).order_by("publishdate").first()
    _previous = Post.objects.filter(course=_course, publishdate__lt=_post.publishdate).exclude(id=_post.id).order_by("publishdate").reverse().first()

    if _next is not None:
        state["blog_next"] = _next.id
    else:
        state["blog_next"] = None

    if _previous is not None:
        state["blog_previous"] = _previous.id
    else:
        state["blog_previous"] = None

    def get():
        return render(request, "com/blog.html", {"state": state,
                                                 "user": user,
                                                 "post": _post})

    def post():
        return render(request, "com/blog.html", {"state": state,
                                                 "user": user,
                                                 "post": _post})

    return resolve_http_method(request, [get, post])


# OnTrack Screen
@oneplus_state_required
@oneplus_login_required
def ontrack(request, state, user):
    #get on track state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    _modules = Module.objects.filter(course=_course)

    # Calculate achieved score
    for m in _modules:
        _answers = _participant.participantquestionanswer_set.filter(question__bank__module__id=m.id)
        if _answers.count() < 10:
            m.score = -1
        else:
            m.score = _answers.filter(correct=True).count() / _answers.count() * 100

    def get():
        return render(request, "prog/ontrack.html", {"state": state,
                                                     "user": user,
                                                     "modules": _modules})

    def post():
        return render(request, "prog/ontrack.html", {"state": state,
                                                     "user": user,
                                                     "modules": _modules})

    return resolve_http_method(request, [get, post])


# Leaderboard Screen
@oneplus_state_required
@oneplus_login_required
def leader(request, state, user):
    #get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _participant.me = True
    request.session["state"]["leader_region"] = "Countrywide"

    def get():
        request.session["state"]["leader_menu"] = False
        request.session["state"]["leader_place"] = Participant.objects.filter(classs=_participant.classs, points__gt=_participant.points).count() + 1

        _learners = \
            list(Participant.objects.filter(
                classs=_participant.classs,
                points__gt=_participant.points).order_by("points")[:4]) \
            + list([_participant]) \
            + list(Participant.objects.filter(
                classs=_participant.classs,
                points__lt=_participant.points).order_by("points").reverse()[:5])

        return render(request, "prog/leader.html", {"state": state,
                                                    "user": user,
                                                    "learners": _learners})

    def post():
        #show region menu?
        if "leader_menu" in request.POST:
            request.session["state"]["leader_menu"] = request.POST["leader_menu"] != 'True'
        elif "region" in request.POST:
            request.session["state"]["leader_menu"] = False
            request.session["state"]["leader_region"] = request.POST["region"]

        if request.session["state"]["leader_region"] != "Countrywide":
            _learners = \
                list(Participant.objects.filter(
                    classs=_participant.classs,
                    points__gt=_participant.points,
                    learner__area=request.session["state"]["leader_region"]).order_by("points")[:4]) \
                + list([_participant]) \
                + list(Participant.objects.filter(
                    classs=_participant.classs,
                    points__lt=_participant.points,
                    learner__area=request.session["state"]["leader_region"]).order_by("points").reverse()[:5])

            request.session["state"]["leader_place"] = \
                Participant.objects.filter(classs=_participant.classs,
                                           points__gt=_participant.points,
                                           learner__area=request.session["state"]["leader_region"]).count() + 1
        else:
            _learners = \
                list(Participant.objects.filter(
                    classs=_participant.classs,
                    points__gt=_participant.points).order_by("points")[:4]) \
                + list([_participant]) \
                + list(Participant.objects.filter(
                    classs=_participant.classs,
                    points__lt=_participant.points).order_by("points").reverse()[:5])

            request.session["state"]["leader_place"] = \
                Participant.objects.filter(classs=_participant.classs,
                                           points__gt=_participant.points).count() + 1

        request.session["state"]["leader_regions"] = list([{"area":"Countrywide"}]) + list(Learner.objects.values("area").distinct().all())

        return render(request, "prog/leader.html", {"state": state,
                                                    "user": user,
                                                    "learners": _learners})

    return resolve_http_method(request, [get, post])


# Points Screen
@oneplus_state_required
@oneplus_login_required
def points(request, state, user):
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    _modules = Module.objects.filter(course=_course)

    def get():
        return render(request, "prog/points.html", {"state": state,
                                                    "user": user,
                                                    "modules": _modules})

    def post():
        return render(request, "prog/points.html", {"state": state,
                                                    "user": user,
                                                    "modules": _modules})

    return resolve_http_method(request, [get, post])


# Badges Screen
@oneplus_state_required
@oneplus_login_required
def badges(request, state, user):
    #get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _course = _participant.classs.course
    _allscenarios = GamificationScenario.objects.exclude(badge__isnull=True).filter(course=_course).prefetch_related("badge")
    _badges = [scenario.badge for scenario in _allscenarios]

    #Link achieved badges
    for x in _badges:
        if _participant.badgetemplate.filter(pk=x.id).count() > 0:
            x.achieved = True

    def get():
        return render(request, "prog/badges.html", {"state": state,
                                                    "user": user,
                                                    "badges": _badges,
                                                    "participant": _participant})

    def post():
        return render(request, "prog/badges.html", {"state": state,
                                                    "user": user,
                                                    "badges": _badges,
                                                    "participant": _participant})

    return resolve_http_method(request, [get, post])


# About Screen
@oneplus_state_required
def about(request, state):
    def get():
        return render(request, "misc/about.html", {"state": state})

    def post():
        return render(request, "misc/about.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Contact Screen
@oneplus_state_required
def contact(request, state):
    def get():
        return render(request, "misc/contact.html", {"state": state})

    def post():
        return render(request, "misc/contact.html", {"state": state})

    return resolve_http_method(request, [get, post])