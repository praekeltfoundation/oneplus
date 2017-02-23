from __future__ import division
import re
from functools import wraps
from haystack.query import SearchQuerySet
from django.shortcuts import render
from django.contrib.auth import authenticate, logout
from django.shortcuts import HttpResponse, redirect, render
from django.http import HttpResponseRedirect
from .forms import SmsPasswordForm, ResetPasswordForm
from django.core.mail import mail_managers
from oneplus.forms import LoginForm
from .views import oneplus_state_required, oneplus_login_required, oneplus_check_user
from auth.models import CustomUser
from communication.models import SmsQueue
from core.models import Learner, ParticipantQuestionAnswer, Setting
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from haystack.exceptions import SearchBackendError
from django.core.urlresolvers import reverse
from datetime import datetime
from lockout import LockedOut
from .validators import validate_mobile, validate_sign_up_form, validate_sign_up_form_normal, \
    validate_sign_up_form_school_confirm,  validate_profile_form, validate_accept_terms_form
from django.db.models import Count
from organisation.models import School
from core.models import Class, Participant
from content.models import Event
from core.common import PROVINCES
from communication.utils import VumiSmsApi

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
                    try:
                        registered = is_registered(user)
                    except:
                        save_user_session_no_participant(request, user)
                        if Learner.objects.filter((Q(enrolled='0') | Q(grade=None) | Q(grade='')) &
                                                  Q(id=request.session['user']['id'])).exists():
                            return redirect("auth.return_signup")
                        else:
                            raise
                    class_active = is_class_active(user)
                    if registered is not None and class_active:
                        save_user_session(request, registered, user)
                        if Learner.objects.filter(id=request.session['user']['id'], enrolled="0").exists():
                            return redirect("auth.return_signup")

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
                        elif len(par) < 1:
                            subject = ' '.join([
                                'No participants active -',
                                usr.first().first_name,
                                usr.first().last_name,
                                '-',
                                usr.first().username
                            ])
                            message = '\n'.join([
                                'Student: ' + usr.first().first_name + ' ' + usr.first().last_name,
                                'Msisdn: ' + usr.first().username,
                                'is unable to login due to having no active participants.',
                                'To fix this, a participant will have to be activated/created.'
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

                        if event:
                            allowed, event_participant_rel = par.first().can_take_event(event)
                            if allowed:
                                return redirect("learn.event_splash_page")
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
            return render(request, "auth/login.html", {"state": state,
                                                       "form": form})

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


def create_learner(first_name, last_name, mobile, country, school, grade):
    return Learner.objects.create(first_name=first_name,
                                  last_name=last_name,
                                  mobile=mobile,
                                  username=mobile,
                                  country=country,
                                  school=school,
                                  grade=grade)


def create_participant(learner, classs):
    return Participant.objects.create(learner=learner,
                                      classs=classs,
                                      datejoined=datetime.now())


def set_learner_password(learner):
    # generate random password
    password = CustomUser.objects.make_random_password(length=4, allowed_chars='0123456789')
    learner.set_password(password)
    learner.save()
    return password


def send_welcome_sms(learner, password):
    # sms the learner their dig-it password
    sms_message = Setting.objects.get(key="WELCOME_SMS")
    learner.generate_unique_token()
    token = learner.unique_token

    vumi_api = VumiSmsApi()
    obj, sent = vumi_api.send(learner.mobile, sms_message.value % (password, token), None, None)

    if not sent:
        SmsQueue.objects.create(message=sms_message.value % (password, token),
                                send_date=datetime.now(),
                                msisdn=learner.mobile)

    learner.welcome_message_sent = True
    learner.save()


@available_space_required
def signup_form(request):

    def get():
        return render(request, "auth/signup_form.html", {"provinces": PROVINCES})

    def post():
        data, errors = validate_sign_up_form(request.POST)

        if not errors:
            return render(request, "auth/signup_form_normal.html", {"data": data,
                                                                    "provinces": PROVINCES})
        else:
            return render(request, "auth/signup_form.html", {"provinces": PROVINCES,
                                                             "data": data,
                                                             "errors": errors})

    return resolve_http_method(request, [get, post])


@available_space_required
def signup_form_normal(request):
    def get():
        return render(request, "auth/signup_form.html", {"provinces": PROVINCES})

    def post():
        data, errors = validate_sign_up_form(request.POST)
        if errors:
            return render(request, "auth/signup_form.html", {"provinces": PROVINCES,
                                                             "data": data,
                                                             "errors": errors})
        normal_data, normal_errors = validate_sign_up_form_normal(request.POST)
        data.update(normal_data)
        errors.update(normal_errors)

        if not errors:
            if "school_dirty" in data:
                school_list = None
                try:
                    school_list = SearchQuerySet()\
                        .filter(province=data['province'], name__fuzzy=data['school_dirty'])\
                        .values('pk', 'name')[:10]
                    for entry in school_list:
                        entry['id'] = entry.pop('pk')
                except:

                    if not school_list or len(school_list) == 0:
                        school_list = School.objects.filter(province=data['province'],
                                                            name__icontains=data['school_dirty']).values()[:10]

                if len(school_list) > 0:
                    return render(request, "auth/signup_school_confirm.html", {"provinces": PROVINCES,
                                                                               "data": data,
                                                                               "school_list": school_list})
                else:
                    errors.update({"school_dirty_error": "No schools were a close enough match."})
                    return render(request, "auth/signup_form_normal.html", {"provinces": PROVINCES,
                                                                            "data": data,
                                                                            "errors": errors})
            else:
                errors.update({"school_error": "Unknown school selected."})
                return render(request, "auth/signup_form_normal.html", {"provinces": PROVINCES,
                                                                        "data": data,
                                                                        "errors": errors})
        else:
            return render(request, "auth/signup_form_normal.html", {"provinces": PROVINCES,
                                                                    "data": data,
                                                                    "errors": errors})

    return resolve_http_method(request, [get, post])


@available_space_required
def signup_school_confirm(request):
    def get():
        return render(request, "auth/signup_form.html", {"provinces": PROVINCES})

    def post():
        data, errors = validate_sign_up_form(request.POST)
        if errors:
            return render(request, "auth/signup_form.html", {"provinces": PROVINCES,
                                                             "data": data,
                                                             "errors": errors})
        normal_data, normal_errors = validate_sign_up_form_normal(request.POST)
        data.update(normal_data)
        errors.update(normal_errors)
        if normal_errors:
            return render(request, "auth/signup_form_normal.html", {"provinces": PROVINCES,
                                                                    "data": data,
                                                                    "errors": errors})
        school_data, school_errors = validate_sign_up_form_school_confirm(request.POST)
        data.update(school_data)
        errors.update(school_errors)

        if not errors:
            if data["school"] != "other":
                school = School.objects.get(id=data["school"])
                class_name = "%s - %s" % (school.name, data['grade'])
                try:
                    classs = Class.objects.get(name=class_name)
                except ObjectDoesNotExist:
                    course = data["course"]
                    classs = Class.objects.create(
                        name=class_name,
                        description="%s open class for %s" % (school.name, data['grade']),
                        province=data["province"],
                        type=Class.CT_OPEN,
                        course=course)
                # create learner
                new_learner = create_learner(first_name=data["first_name"],
                                             last_name=data["surname"],
                                             mobile=data["cellphone"],
                                             country="South Africa",
                                             school=school,
                                             grade=data["grade"])

                # create participant
                create_participant(new_learner, classs)

                password = set_learner_password(new_learner)
                send_welcome_sms(new_learner, password)

                return render(request, "auth/signedup.html")
            else:
                errors.update({"school_error": "Unknown school selected."})
                return render(request, "auth/signup_school_confirm.html", {"provinces": PROVINCES,
                                                                           "data": data,
                                                                           "errors": errors})
        else:
            return render(request, "auth/signup_school_confirm.html", {"provinces": PROVINCES,
                                                                       "data": data,
                                                                       "errors": errors})

    return resolve_http_method(request, [get, post])


@oneplus_state_required
def return_signup(request, state):
    user = request.session.get("user", None)
    if not user:
        return redirect('auth.login')
    if Learner.objects.filter(id=user['id']).exclude(Q(enrolled='0') | Q(grade=None) | Q(grade='')).exists():
        return redirect('learn.home')
    learner = Learner.objects.get(id=user['id'])

    def get():
        try:
            school = learner.school
            province = school.province
        except:
            school = None
            province = None

        data = {
            "first_name": learner.first_name,
            "grade": learner.grade,
            "province": province,
            "school_dirty": school,
        }
        return render(request, "auth/return_signup.html", {"provinces": PROVINCES, "data": data})

    def post():
        data, errors = validate_sign_up_form_normal(request.POST)
        data.update({"first_name": learner.first_name})

        if not errors:
            if "school_dirty" in data:
                school_list = None
                try:
                    school_list = SearchQuerySet()\
                        .filter(province=data['province'], name__fuzzy=data['school_dirty'])\
                        .values('pk', 'name')[:10]
                    for entry in school_list:
                        entry['id'] = entry.pop('pk')
                except:
                    school_list = None
                finally:
                    if not school_list or len(school_list) == 0:
                        school_list = School.objects.filter(province=data['province'],
                                                            name__icontains=data['school_dirty']).values()[:10]

                if len(school_list) > 0:
                    return render(request, "auth/return_signup_school_confirm.html", {"provinces": PROVINCES,
                                                                                      "data": data,
                                                                                      "school_list": school_list})
                else:
                    errors.update({"school_dirty_error": "No schools were a close enough match."})
                    return render(request, "auth/return_signup.html", {"provinces": PROVINCES,
                                                                       "data": data,
                                                                       "errors": errors})
            else:
                errors.update({"school_error": "Unknown school selected."})
                return render(request, "auth/return_signup.html", {"provinces": PROVINCES,
                                                                   "data": data,
                                                                   "errors": errors})
        else:
            return render(request, "auth/return_signup.html", {"provinces": PROVINCES,
                                                               "data": data,
                                                               "errors": errors})

    return resolve_http_method(request, [get, post])


@oneplus_state_required
def return_signup_school_confirm(request, state):
    user = request.session.get("user", None)
    if not user:
        return redirect('auth.login')
    if Learner.objects.filter(id=user['id']).exclude(Q(enrolled='0') | Q(grade=None) | Q(grade='')).exists():
        return redirect('learn.home')
    learner = Learner.objects.get(id=user['id'])

    def get():
        return redirect("auth.return_signup")

    def post():
        data, errors = validate_sign_up_form_normal(request.POST)
        data.update({"first_name": learner.first_name})
        if errors:
            return render(request, "auth/return_signup.html", {"provinces": PROVINCES,
                                                               "data": data,
                                                               "errors": errors})
        school_data, school_errors = validate_sign_up_form_school_confirm(request.POST)
        data.update(school_data)
        errors.update(school_errors)

        if not errors:
            if data["school"] != "other":
                school = School.objects.get(id=data["school"])
                class_name = "%s - %s" % (school.name, data['grade'])
                try:
                    classs = Class.objects.get(name=class_name)
                except ObjectDoesNotExist:
                    course = data["course"]
                    classs = Class.objects.create(
                        name=class_name,
                        description="%s open class for %s" % (school.name, data['grade']),
                        province=data["province"],
                        type=Class.CT_OPEN,
                        course=course)

                # update learner
                learner.school = school
                learner.grade = data["grade"]
                learner.enrolled = "1"
                learner.save()

                # create participant
                Participant.objects.filter(learner=learner, is_active=True).update(is_active=False)
                participant = create_participant(learner, classs)
                request.session["user"]["participant_id"] = participant.id
                return redirect("learn.home")
            else:
                errors.update({"school_error": "Unknown school selected."})
                return render(request, "auth/return_signup_school_confirm.html", {"provinces": PROVINCES,
                                                                                  "data": data,
                                                                                  "errors": errors})
        else:
            return render(request, "auth/return_signup_school_confirm.html", {"provinces": PROVINCES,
                                                                              "data": data,
                                                                              "errors": errors})

    return resolve_http_method(request, [get, post])


def no_sms(request):

    def get():
        return render(request, "auth/no_sms.html")

    return resolve_http_method(request, [get])


@oneplus_state_required
def signout(request, state):
    logout(request)

    def get():
        return HttpResponseRedirect("/")

    def post():
        return HttpResponseRedirect("/")

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
        if "user_exists" in request.session and "username" in request.session:
            exists = request.session["user_exists"]
            username = request.session["username"]
        else:
            return get()
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
    return Participant.objects.filter(learner=user.learner, is_active=True).latest('datejoined')


def save_user_session(request, registered, user):

    request.session["user"] = {}
    request.session["user"]["id"] = user.learner.id
    request.session["user"]["name"] = user.learner.first_name
    request.session["user"]["participant_id"] \
        = registered.id
    request.session["user"]["place"] = 0  # TODO
    registered.award_scenario("LOGIN", None, special_rule=True)

    # update last login date
    user.last_login = datetime.now()
    user.save()


def save_user_session_no_participant(request, user):
    request.session["user"] = {}
    request.session["user"]["id"] = user.learner.id
    request.session["user"]["name"] = user.learner.first_name
    request.session["user"]["place"] = 0  # TODO

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


def sms_reset_password_link(request):
    def get():
        return render(
            request,
            "auth/sms_password_reset.html",
            {
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
                learner = Learner.objects.get(username=form.cleaned_data["msisdn"])

                # Generate reset password link
                learner.generate_reset_password_token()

                # Message
                message = "Use the following link to reset your password: http://www.dig-it.me/r/%s" % \
                          learner.pass_reset_token

                sms, sent = vumi.send(learner.mobile, message, None, None)

                if sent:
                    message = "Link has been SMSed to you."
                    success = True
                else:
                    message = "Oops! Something went wrong! " \
                              "Please try enter your number again or "

                    success = False
                learner.save()

                return render(
                    request,
                    "auth/sms_password_reset.html",
                    {
                        "sent": True,
                        "message": message,
                        "success": success
                    }
                )

            except Learner.DoesNotExist:
                message = "The number you have entered is not registered."

        else:
            message = "Please enter your mobile number."
            form = SmsPasswordForm()

        return render(
            request,
            "auth/sms_password_reset.html",
            {
                "form": form,
                "message": message
            }
        )

    return resolve_http_method(request, [get, post])


def reset_password(request, token):
    # Get user based on token + expiry date
    user = CustomUser.objects.filter(
        pass_reset_token=token,
        pass_reset_token_expiry__gte=datetime.now()
    ).first()
    if not user:
        return HttpResponseRedirect("/")

    def get():
        return render(
            request,
            "auth/reset_password.html",
            {
                "name": user.first_name,
                "form": ResetPasswordForm()
            }
        )

    def post():
        form = ResetPasswordForm(request.POST)
        changed = False
        message = None

        if form.is_valid():
            password = form.cleaned_data["password"]
            password_2 = form.cleaned_data["password_2"]

            if password == password_2:
                #save new password
                user.password = make_password(password)
                user.save()
                changed = True
                message = "Password changed."
            else:
                message = "Passwords do not match."

            return render(
                request,
                "auth/reset_password.html",
                {
                    "name": user.first_name,
                    "form": ResetPasswordForm(),
                    "changed": changed,
                    "message": message
                }
            )

        error = "Please enter your new password."
        return render(
            request,
            "auth/reset_password.html",
            {
                "name": user.first_name,
                "form": ResetPasswordForm(),
                "changed": changed,
                "message": message
            }
        )

    return resolve_http_method(request, [get, post])


@oneplus_login_required
def profile(request, state, user):
    def get():
        try:
            learner = Learner.objects.get(id=user['id'])
            data = {
                'first_name': learner.first_name,
                'grade': learner.grade,
                'last_name': learner.last_name,
                'mobile': learner.mobile,
                'province': learner.school.province,
                'school': learner.school.name,
                'public_share': learner.public_share,
            }
        except Exception as e:
            data = {}
        return render(request, "auth/profile.html", {'data': data, 'user': user})

    return resolve_http_method(request, [get])


@oneplus_login_required
def edit_profile(request, state, user):
    def get():
        try:
            learner = Learner.objects.get(id=user['id'])
            data = {
                'first_name': learner.first_name,
                'grade': learner.grade,
                'last_name': learner.last_name,
                'mobile': learner.mobile,
                'province': learner.school.province,
                'school': learner.school.name,
                'public_share': learner.public_share,
            }
        except Exception as e:
            data = {}
        return render(request, "auth/profile.html", {'data': data, 'editing': True, 'user': user})

    def post():
        errors = None
        try:
            learner = Learner.objects.get(id=user['id'])
            validated_data, errors = validate_profile_form(request.POST, learner)

            if not errors or len(errors) == 0:
                learner.first_name = validated_data['first_name']
                learner.last_name = validated_data['last_name']
                learner.mobile = validated_data['mobile']
                learner.public_share = validated_data['public_share']
                learner.save()

            data = {
                'first_name': request.POST.get('first_name', learner.first_name),
                'grade': request.POST.get('grade', learner.grade),
                'last_name': request.POST.get('last_name', learner.last_name),
                'mobile': request.POST.get('mobile', learner.mobile),
                'province': request.POST.get('province', learner.school.province),
                'school': request.POST.get('school', learner.school.name),
                'public_share': request.POST.get('public_share', learner.public_share),
            }

        except Exception as e:
            data = {}
            errors = {'unknown_error': 'An unknown error has occurred.'}

        if not errors or len(errors) < 1:
            return redirect(reverse("auth.profile"))
        else:
            return render(request, "auth/profile.html", {'data': data, 'editing': True, 'errors': errors, 'user': user})

    return resolve_http_method(request, [get, post])

@oneplus_check_user
def accept_terms(request, state, user):
    if 'user' in request.session.keys():
        user = request.session['user']
    else:
        user = None

    def get():
        return render(request, "auth/accept_terms.html", {"state": state, "user": user})

    def post():
        data, errors = validate_accept_terms_form()

        if errors is None:
            learner = Learner.objects.get(id=user['id'])
            learner.terms_accept = True
            learner.save()
        else:
            return render(request, "auth/accept_terms.html",
                          {"state": state,
                           "user": user,
                           "errors": {'terms_errors': "You must accept the terms and conditions to continue."}})

        return redirect('learn.home')

    return resolve_http_method(request, [get, post])
