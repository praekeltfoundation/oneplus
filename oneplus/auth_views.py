from __future__ import division
from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, logout
from django.core.mail import mail_managers
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password
from lockout import LockedOut
import koremutake
from django.db.models import Count
from django.db.models import Q

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, logout
from .forms import SmsPasswordForm
from django.core.mail import mail_managers
from oneplus.forms import LoginForm
from .views import *
from communication.models import *
from core.models import *
from oneplus.models import *
from auth.models import CustomUser
from communication.utils import VumiSmsApi
from communication.utils import get_autologin_link
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password
from lockout import LockedOut
import koremutake
from .validators import *
from django.db.models import Count
from django.db.models import Q
from organisation.models import School, Course
from core.models import Class, Participant
from oneplusmvp import settings
from content.models import Event, EventParticipantRel

__author__ = 'herman'


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
                    class_active = is_class_active(user)
                    if registered is not None and class_active:
                        save_user_session(request, registered, user)

                        usr = Learner.objects.filter(username=form.cleaned_data["username"])
                        par = Participant.objects.filter(learner=usr, is_active=True)

                        if len(par) > 1:
                            subject = ' '.join([
                                'Multiple participants active -',
                                usr.first().first_name,
                                usr.first().last_name,
                                '-',
                                usr.first().username
                            ])
                            message = '\n'.join([
                                'Student: ' + usr.first().first_name + ' ' + usr.first().last_name,
                                'Msisdn: ' + usr.first().username,
                                'is unable to login due to having multiple active participants.',
                                'To fix this, some participants  will have to be deactivated.'
                            ])

                            mail_managers(
                                subject=subject,
                                message=message,
                                fail_silently=False
                            )
                            return render(request, "misc/account_problem.html")

                        event = Event.objects.filter(course=par.first().classs.course,
                                                     activation_date__lte=datetime.now(),
                                                     deactivation_date__gt=datetime.now()
                                                     ).first()
                        if event and not EventParticipantRel.objects.filter(event=event, participant=par,
                                                                            results_seen=True):
                            return redirect("learn.event_splash_page")
                        elif ParticipantQuestionAnswer.objects.filter(participant=par).count() == 0:
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


def space_available():
    total_reg = Participant.objects.aggregate(registered=Count('id'))
    maximum = int(Setting.objects.get(key="MAX_NUMBER_OF_LEARNERS").value)
    num = maximum - total_reg.get('registered')
    if num > 0:
        return True, num
    else:
        return False, 0


def available_space_required(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        space, num_spaces = space_available()

        if space:
            return f(request, *args, **kwargs)
        else:
            return redirect("misc.welcome")
    return wrap


@available_space_required
def signup(request):
    def get():
        space, num_spaces = space_available()
        return render(
            request,
            "auth/signup.html",
            {
                "space": space,
                "num_spaces": num_spaces
            }
        )

    def post():
        if 'yes' in request.POST.keys():
            return redirect("auth.signup_form")
        else:
            return redirect("misc.welcome")

    return resolve_http_method(request, [get, post])


def validate_mobile(mobile):
    pattern_both = "^(\+\d{1,2})?\d{10}$"
    match = re.match(pattern_both, mobile)
    if match:
        return mobile
    else:
        return None


def create_learner(first_name, last_name, mobile, country, school, grade):
    return Learner.objects.create(first_name=first_name,
                                  last_name=last_name,
                                  mobile=mobile,
                                  username=mobile,
                                  country=country,
                                  school=school,
                                  grade=grade)


def create_participant(learner, classs):
    Participant.objects.create(learner=learner,
                               classs=classs,
                               datejoined=datetime.now())


@available_space_required
def signup_form(request):
    provinces = ("Eastern Cape", "Free State", "Gauteng", "KwaZulu-Natal", "Limpopo", "Mpumalanga", "North West",
                 "Northern Cape", "Western Cape")
    schools = School.objects.exclude(name__in=provinces)
    classes = Class.objects.all()
    province_schools = School.objects.filter(name__in=provinces)

    def get():
        return render(request, "auth/signup_form.html", {"schools": schools,
                                                         "classes": classes,
                                                         "provinces": province_schools})

    def post():
        data = {}
        errors = {}

        if "first_name" in request.POST.keys() and request.POST["first_name"]:
            data["first_name"] = request.POST["first_name"]
        else:
            errors["first_name_error"] = "This must be completed"

        if "surname" in request.POST.keys() and request.POST["surname"]:
            data["surname"] = request.POST["surname"]
        else:
            errors["surname_error"] = "This must be completed"

        if "cellphone" in request.POST.keys() and request.POST["cellphone"]:
            cellphone = request.POST["cellphone"]
            if validate_mobile(cellphone):
                if CustomUser.objects.filter(Q(mobile=cellphone) | Q(username=cellphone)).exists():
                    errors["cellphone_error"] = "registered"
                else:
                    data["cellphone"] = cellphone
            else:
                errors["cellphone_error"] = "Enter a valid cellphone number"
        else:
            errors["cellphone_error"] = "This must be completed"

        enrolled = True
        if "enrolled" in request.POST.keys() and request.POST["enrolled"]:
            data["enrolled"] = request.POST["enrolled"]
            if data["enrolled"] == '1':
                enrolled = False
        else:
            errors["enrolled_error"] = "This must be completed"

        if enrolled:
            if "school" in request.POST.keys() and request.POST["school"]:
                data["school"] = request.POST["school"]
                try:
                    School.objects.get(id=data["school"])
                except School.DoesNotExist:
                    errors["school_error"] = "Select a Centre/Province"
            else:
                errors["school_error"] = "Select a Centre/Province"

            if "classs" in request.POST.keys() and request.POST["classs"]:
                data["classs"] = request.POST["classs"]
                try:
                    Class.objects.get(id=data["classs"])
                except Class.DoesNotExist:
                    errors["class_error"] = "Select a class"
            else:
                errors["class_error"] = "Select a class"

        else:
            if "province" in request.POST.keys() and request.POST["province"]:
                data["province"] = request.POST["province"]
                try:
                    if School.objects.get(id=data["province"]).name not in provinces:
                        errors["province_error"] = "Select a province"
                except School.DoesNotExist:
                    errors["province_error"] = "Select a province"

        if "grade" in request.POST.keys() and request.POST["grade"]:
            if request.POST["grade"] not in ("Grade 10", "Grade 11"):
                errors["grade_error"] = "Select a grade"
            else:
                data["grade"] = request.POST["grade"]
        else:
            errors["grade_error"] = "This must be completed"

        if not errors:
            if not enrolled:
                province = School.objects.get(id=data["province"])

                # create learner
                new_learner = create_learner(first_name=data["first_name"],
                                             last_name=data["surname"],
                                             mobile=data["cellphone"],
                                             country="South Africa",
                                             school=province,
                                             grade=data["grade"])

                if data["grade"] == "Grade 10":
                    try:
                        classs = Class.objects.get(name=settings.GRADE_10_OPEN_CLASS_NAME)
                    except Class.DoesNotExist:
                        try:
                            course = Course.objects.get(name=settings.GRADE_10_COURSE_NAME)
                        except Course.DoesNotExist:
                            course = Course.objects.create(name=settings.GRADE_10_COURSE_NAME)
                        classs = Class.objects.create(name=settings.GRADE_10_OPEN_CLASS_NAME, course=course)
                else:
                    try:
                        classs = Class.objects.get(name=settings.GRADE_11_OPEN_CLASS_NAME)
                    except Class.DoesNotExist:
                        try:
                            course = Course.objects.get(name=settings.GRADE_11_COURSE_NAME)
                        except Course.DoesNotExist:
                            course = Course.objects.create(name=settings.GRADE_11_COURSE_NAME)
                        classs = Class.objects.create(name=settings.GRADE_11_OPEN_CLASS_NAME, course=course)

                create_participant(new_learner, classs)

            else:
                school = School.objects.get(id=data["school"])
                # create learner
                new_learner = create_learner(first_name=data["first_name"],
                                             last_name=data["surname"],
                                             mobile=data["cellphone"],
                                             country="South Africa",
                                             school=school,
                                             grade=data["grade"])

                classs = Class.objects.get(id=data["classs"])

                # create participant
                create_participant(new_learner, classs)

            # generate random password
            password = CustomUser.objects.make_random_password(length=8)
            new_learner.set_password(password)
            new_learner.save()

            # sms the learner their OnePlus password
            sms_message = Setting.objects.get(key="WELCOME_SMS")
            new_learner.generate_unique_token()
            token = new_learner.unique_token
            SmsQueue.objects.create(message=sms_message.value % (password, token),
                                    send_date=datetime.now(),
                                    msisdn=cellphone)

            new_learner.welcome_message_sent = True
            new_learner.save()

            # inform oneplus about the new learner
            subject = "".join(['New student registered'])
            message = "".join([
                new_learner.first_name + ' ' + new_learner.last_name + ' has registered.'])

            # mail_managers(subject=subject, message=message, fail_silently=False)

            return render(request, "auth/signedup.html")
        else:
            return render(request, "auth/signup_form.html", {"schools": schools,
                                                             "classes": classes,
                                                             "provinces": province_schools,
                                                             "data": data,
                                                             "errors": errors})

    return resolve_http_method(request, [get, post])


@oneplus_state_required
def signout(request, state):
    logout(request)

    def get():
        return HttpResponseRedirect("/")

    def post():
        return HttpResponseRedirect("/")

    return resolve_http_method(request, [get, post])


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
            #  Initialize vumigo sms
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


@oneplus_state_required
@oneplus_login_required
def change_details(request, state, user):
    def render_error(error_field, error_message):
        return render(
            request,
            "auth/change_details.html",
            {
                "state": state,
                "user": user,
                "error_field": error_field,
                "error_message": error_message
            }
        )

    def get():
        return render(
            request,
            "auth/change_details.html",
            {
                "state": state,
                "user": user
            }
        )

    def post():

        mobile_change = False
        email_change = False
        changes = []
        learner = Learner.objects.get(id=request.session["user"]["id"])

        # are there any changes to be made
        if "old_number" in request.POST.keys() or "new_number" in request.POST.keys() or \
                "old_email" in request.POST.keys() or "new_email" in request.POST.keys():

            error_field = ""
            error_message = ""

            # check if NUMBER wants to be changed
            if "old_number" in request.POST.keys() and request.POST["old_number"] != "" or \
                    "new_number" in request.POST.keys() and request.POST["new_number"] != "":

                old_mobile = request.POST["old_number"]

                if validate_mobile(old_mobile) is None:
                    error_field = "old_mobile_error"
                    error_message = "Please enter a valid mobile number."
                    return render_error(error_field, error_message)

                if learner.mobile != old_mobile:
                    error_field = "old_mobile_error"
                    error_message = "This number is not associated with this account."
                    return render_error(error_field, error_message)

                new_mobile = request.POST["new_number"]
                validated_mobile = validate_mobile(new_mobile)
                if not validated_mobile:
                    error_field = "new_mobile_error"
                    error_message = "Please enter a valid mobile number."
                    return render_error(error_field, error_message)

                if new_mobile == old_mobile:
                    error_field = "new_mobile_error"
                    error_message = "You cannot change your number to your current number."
                    return render_error(error_field, error_message)

                new_mobile = validated_mobile

                # check if a user with the new mobile number already exits
                existing = Learner.objects.filter(mobile=new_mobile)
                if existing:
                    error_field = "new_mobile_error"
                    error_message = "A user with this mobile number (%s) already exists." % new_mobile
                    return render_error(error_field, error_message)

                mobile_change = True

            # check if EMAIL wants to be changed
            if "old_email" in request.POST.keys() and request.POST["old_email"] != "" or \
                    "new_email" in request.POST.keys() and request.POST["new_email"] != "":

                old_email = request.POST["old_email"]
                if learner.email != old_email:
                    error_field = "old_email_error"
                    error_message = "This email is not associated with this account."
                    return render_error(error_field, error_message)

                new_email = request.POST["new_email"]

                if new_email == old_email:
                    error_field = "new_email_error"
                    error_message = "This is your current email."
                    return render_error(error_field, error_message)

                if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                    error_field = "new_email_error"
                    error_message = "Please enter a valid email."
                    return render_error(error_field, error_message)

                # check if a user with this email number already exits
                existing = Learner.objects.filter(email=new_email)
                if existing:
                    error_field = "new_email_error"
                    error_message = "A user with this email (%s) already exists." % new_email
                    return render_error(error_field, error_message)

                email_change = True

            if mobile_change:
                learner.mobile = new_mobile
                learner.username = new_mobile
                learner.save()
                line = {"change_details":  "Your number has been changed to %s." % new_mobile}
                changes.append(line)

            if email_change:
                learner.email = new_email
                learner.save()
                line = {"change_details":  "Your email has been changed to %s." % new_email}
                changes.append(line)

        else:
            line = {"change_details":  "No changes made."}
            changes.append(line)

        return render(request,
                      "auth/change_details_confirmation.html",
                      {
                          "state": state,
                          "user": user,
                          "changes": changes
                      })

    return resolve_http_method(request, [get, post])


def is_class_active(user):
    return Participant.objects.filter(learner=user.learner, classs__is_active=True)


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