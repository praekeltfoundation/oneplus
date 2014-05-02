from django.shortcuts import render, get_object_or_404, HttpResponse
from django.http import HttpResponseRedirect
from forms import *
from core.models import *
from oneplus.models import *
from django.views.generic import View


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
            # Check if this is a registered learner
            _learner = Learner.objects.filter(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"]).first()

            if _learner is not None:
                # Check which OnePlus course learner is on
                _registered = None
                for _parti in Participant.objects.filter(learner=_learner):
                    if _parti.classs.course.name == "Grade 12 Math":
                        _registered = _parti

                if _parti is not None:
                    request.session["user"] = {}
                    request.session["user"]["id"] = _learner.id
                    request.session["user"]["name"] = _learner.firstname
                    request.session["user"]["participant_id"] = _registered.id
                    request.session["user"]["points"] = _registered.points
                    request.session["user"]["place"] = 0  # TODO
                    request.session["user"]["badges"] = _registered.badgetemplate.count()
                    request.session["user"]["latest"] = _registered.badgetemplate.last().name

                    return HttpResponseRedirect("welcome")
                else:
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
@oneplus_login_required
def welcome(request, state, user):
    def get():
        return render(request, "learn/welcome.html", {"state": state,
                                                      "user": user})

    def post():
        return render(request, "learn/welcome.html", {"state": state,
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
            if _option.correct:
                _learnerstate.active_result = True
                _learnerstate.save()
                return HttpResponseRedirect("right")
            else:
                _learnerstate.active_result = False
                _learnerstate.save()
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
                                                       "question": _learnerstate.active_question})
        else:
            return HttpResponseRedirect("wrong")

    def post():
        if _learnerstate.active_result:
            return render(request, "learn/right.html", {"state": state,
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
                                                       "question": _learnerstate.active_question})
        else:
            return HttpResponseRedirect("right")

    def post():
        if not _learnerstate.active_result:
            return render(request, "learn/wrong.html", {"state": state,
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
    _posts = Post.objects.filter(course=_course).order_by("publishdate").reverse()[:3]

    def get():
        return render(request, "com/inbox.html", {"state": state})

    def post():
        return render(request, "com/inbox.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Chat Screen
@oneplus_state_required
@oneplus_login_required
def chat(request, state, user):
    def get():
        return render(request, "com/chat.html", {"state": state})

    def post():
        return render(request, "com/chat.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Blog Screen
@oneplus_state_required
@oneplus_login_required
def blog(request, state, user):
    #get blog entry
    _course = Participant.objects.get(pk=user["participant_id"]).classs.course
    _posts = Post.objects.filter(course=_course).order_by("publishdate").reverse()[:3]

    request.session["state"]["page_max"] = _posts.count()-1
    if "page" not in state.keys():
        request.session["state"]["page"] = 0


    def get():
        return render(request, "com/blog.html", {"state": state, "post": _posts[state["page"]]})

    def post():
        # next/previous action provided
        if "previous" in request.POST.keys():
            state["page"] = state["page"] - 1

        if "next" in request.POST.keys():
            state["page"] = state["page"] + 1

        return render(request, "com/blog.html", {"state": state, "post": _posts[state["page"]]})

    return resolve_http_method(request, [get, post])


# OnTrack Screen
@oneplus_state_required
@oneplus_login_required
def ontrack(request, state, user):
    def get():
        return render(request, "prog/ontrack.html", {"state": state})

    def post():
        return render(request, "prog/ontrack.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Leaderboard Screen
@oneplus_state_required
@oneplus_login_required
def leader(request, state, user):
    def get():
        return render(request, "prog/leader.html", {"state": state})

    def post():
        return render(request, "prog/leader.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Badges Screen
@oneplus_state_required
@oneplus_login_required
def badges(request, state, user):
    #get learner state
    _participant = Participant.objects.get(pk=user["participant_id"])
    _badges = _participant.badgetemplate

    def get():
        return render(request, "prog/badges.html", {"state": state,
                                                    "participant": _participant})

    def post():
        return render(request, "prog/badges.html", {"state": state,
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


# Investec Screen
@oneplus_state_required
def investec(request, state):
    def get():
        return render(request, "misc/investec.html", {"state": state})

    def post():
        return render(request, "misc/investec.html", {"state": state})

    return resolve_http_method(request, [get, post])


# Preakelt Screen
@oneplus_state_required
def preakelt(request, state):
    def get():
        return render(request, "misc/preakelt.html", {"state": state})

    def post():
        return render(request, "misc/preakelt.html", {"state": state})

    return resolve_http_method(request, [get, post])