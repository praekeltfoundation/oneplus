from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from forms import *
from core.models import *
from oneplus.models import *

def login(request):
    if request.method == "POST":  # If the form has been submitted...
        # ContactForm was defined in the the previous section
        form = LoginForm(request.POST)  # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
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
                return HttpResponseRedirect("getconnected")  # Redirect after POST
    else:
        form = LoginForm()  # An unbound form

    return render(request, "auth/login.html", {"form": form})


def smspassword(request):
    return render(request, "auth/smspassword.html", {})


def getconnected(request):
    return render(request, "auth/getconnected.html", {})


def welcome(request):
    user = request.session["user"]
    if request.session.get("user") is not None:
        return render(request, "learn/welcome.html", {"user": user})
    else:
        return HttpResponseRedirect("login")


def nextchallenge(request):
    user = request.session["user"]
    if request.session.get("user") is not None:
        #get next question
        _pid = request.session["user"]["participant_id"]
        _learnerstate = LearnerState.objects.filter(participant__id=_pid).first()
        if _learnerstate is None:
            _learnerstate = LearnerState(participant=Participant.objects.get(pk=request.session["user"]["participant_id"]))

        if request.method == 'POST':
            # answer provided
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
            # check if new question required then show question
            _learnerstate.getnextquestion()
            return render(request, "learn/next.html", {"user": user, "question": _learnerstate.active_question})

    else:
        return HttpResponseRedirect("login")


def right(request):
    if request.session.get("user") is not None:
        #get next question
        _pid = request.session["user"]["participant_id"]
        _learnerstate = LearnerState.objects.filter(participant__id=_pid).first()
        if _learnerstate is None:
            _learnerstate = LearnerState(participant=Participant.objects.get(pk=request.session["user"]["participant_id"]))

        if (_learnerstate.active_result == True):
            return render(request, "learn/right.html", {"question": _learnerstate.active_question})
        else:
            return HttpResponseRedirect("wrong")
    else:
        return HttpResponseRedirect("login")


def wrong(request):
    if request.session.get("user") is not None:
        #get next question
        _pid = request.session["user"]["participant_id"]
        _learnerstate = LearnerState.objects.filter(participant__id=_pid).first()
        if _learnerstate is None:
            _learnerstate = LearnerState(participant=Participant.objects.get(pk=request.session["user"]["participant_id"]))

        if (_learnerstate.active_result == False):
            return render(request, "learn/wrong.html", {"question": _learnerstate.active_question})
        else:
            return HttpResponseRedirect("right")
    else:
        return HttpResponseRedirect("login")



def discuss(request):
    return render(request, "learn/discuss.html", {})


def inbox(request):
    return render(request, "com/inbox.html", {})


def chat(request):
    return render(request, "com/chat.html", {})


def blog(request):
    return render(request, "com/blog.html", {})


def ontrack(request):
    return render(request, "prog/ontrack.html", {})


def leader(request):
    return render(request, "prog/leader.html", {})


def badges(request):
    return render(request, "prog/badges.html", {})


def about(request):
    return render(request, "misc/about.html", {})


def contact(request):
    return render(request, "misc/contact.html", {})


def investec(request):
    return render(request, "misc/investec.html", {})


def preakelt(request):
    return render(request, "misc/preakelt.html", {})

#def school_list(request):
#    return render(request, "school/list.html", { "allschools": School.objects.all() })


#def school_detail(request, school_id):
#    school = get_object_or_404(School, pk=school_id)
#    return render(request, "school/detail.html", {"school": school})
