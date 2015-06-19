from __future__ import division

from functools import wraps
import json

from django.shortcuts import render, HttpResponse
from django.http import HttpResponseRedirect
from django.core.mail import mail_managers
from django.contrib.auth.decorators import user_passes_test
from django.db import connection
from django.core.urlresolvers import reverse
from .validators import *
from django.shortcuts import render, HttpResponse
from django.http import HttpResponseRedirect
from django.core.mail import mail_managers
from django.contrib.auth.decorators import user_passes_test
from auth.models import CustomUser
from communication.models import Report, Message, Discussion, PostComment, ChatMessage
from core.models import Participant
from oneplus.auth_views import space_available, resolve_http_method
from oneplus.report_utils import get_csv_report, get_xls_report
from oneplus.validators import validate_title, validate_publish_date_and_time, validate_content, gen_username
from oneplus.views import oneplus_state_required, oneplus_login_required


@oneplus_state_required
def welcome(request, state):
    def get():
        space, nums_spaces = space_available()
        return render(request, "misc/welcome.html", {"state": state, "space": space})

    def post():
        return render(request, "misc/welcome.html", {"state": state})

    return resolve_http_method(request, [get, post])


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


def oneplus_check_user(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if "user" in request.session.keys():
            return f(request, user=request.session["user"], *args, **kwargs)
        else:
            return f(request, user=None, *args, **kwargs)
    return wrap


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

        if "contact" in request.POST.keys() and len(request.POST["contact"]) >= 3:
            _contact = request.POST["contact"]
            state['contact'] = _contact
        else:
            state['valid'] = False
            state['valid_message'].append("Mobile number or Email")

        if "comment" in request.POST.keys() and len(request.POST["comment"]) >= 3:
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
def discussion_response(request, disc):
    db_disc = Discussion.objects.filter(id=disc).first()

    if db_disc:
        db_participant = Participant.objects.filter(learner=db_disc.author).first()

        if db_participant is None:
            return HttpResponse("Participant not found")
    else:
        return HttpResponse("Discussion %s not found" % disc)

    ro = None
    response = None

    if db_disc.response:
        ro = 1
        response = db_disc.response

    def get():
        return render(
            request=request,
            template_name="misc/discussion_response.html",
            dictionary={"disc": db_disc, "participant": db_participant, "ro": ro, "response": response}
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
                template_name="misc/discussion_response.html",
                dictionary={
                    "disc": db_disc,
                    "participant": db_participant,
                    "ro": ro,
                    "response": response,
                    "title_error": title_error,
                    "dt_error": dt_error,
                    "content_error": content_error,
                    "v_title": title,
                    "v_date": date,
                    "v_time": time,
                    "v_content": content
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
                question=db_disc.question,
                reply=db_disc
            )

            db_disc.response = disc
            db_disc.save()

            return HttpResponseRedirect("/admin/communication/discussion/")

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def discussion_response_selected(request, disc):
    discs = disc.split(',')
    db_discs = Discussion.objects.filter(id__in=discs, response__isnull=True)

    if db_discs.count() == 0:
        no_discussions = True
    else:
        no_discussions = False

    def get():
        return render(
            request=request,
            template_name='misc/discussion_response_selected.html',
            dictionary={'discs': db_discs, 'no_discs': no_discussions}
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
                template_name='misc/discussion_response_selected.html',
                dictionary={
                    'discs': db_discs,
                    'no_discs': no_discussions,
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
            for db_disc in db_discs:
                disc = Discussion.objects.create(
                    name=gen_username(request.user),
                    description=title,
                    content=content,
                    author=request.user,
                    publishdate=dt,
                    moderated=True,
                    course=db_disc.course,
                    module=db_disc.module,
                    question=db_disc.question,
                    reply=db_disc
                )

                db_disc.response = disc
                db_disc.save()

            return HttpResponseRedirect('/admin/communication/discussion/')

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def blog_comment_response(request, pc):
    db_pc = PostComment.objects.filter(id=pc).first()

    if not db_pc:
        return HttpResponse("PostComment %s not found" % pc)

    ro = None
    response = None

    if db_pc.response:
        ro = 1
        response = db_pc.response

    def get():
        return render(
            request=request,
            template_name="misc/blog_comment_response.html",
            dictionary={
                "pc": db_pc,
                "ro": ro,
                "response": response
            }
        )

    def post():

        dt_error = False
        content_error = False

        dt_error, date, time, dt = validate_publish_date_and_time(request.POST)
        content_error, content = validate_content(request.POST)

        if dt_error or content_error:
            return render(
                request=request,
                template_name="misc/blog_comment_response.html",
                dictionary={
                    "pc": db_pc,
                    "ro": ro,
                    "response": response,
                    "dt_error": dt_error,
                    "content_error": content_error,
                    "v_date": date,
                    "v_time": time,
                    "v_content": content
                }
            )
        else:
            pc = PostComment.objects.create(
                author=request.user,
                content=content,
                publishdate=dt,
                moderated=True,
                post=db_pc.post
            )

            db_pc.response = pc
            db_pc.save()

            return HttpResponseRedirect("/admin/communication/postcomment/")

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def blog_comment_response_selected(request, pc):
    pcs = pc.split(',')
    db_pcs = PostComment.objects.filter(id__in=pcs, response__isnull=True)

    if db_pcs.count() == 0:
        no_pcs = True
    else:
        no_pcs = False

    def get():

        return render(
            request=request,
            template_name='misc/blog_comment_response_selected.html',
            dictionary={'pcs': db_pcs, 'no_pcs': no_pcs}
        )

    def post():

        dt_error = False
        content_error = False
        date = None
        time = None
        content = None

        dt_error, date, time, dt = validate_publish_date_and_time(request.POST)
        content_error, content = validate_content(request.POST)

        if dt_error or content_error:
            return render(
                request=request,
                template_name='misc/blog_comment_response_selected.html',
                dictionary={
                    'pcs': db_pcs,
                    'no_pcs': no_pcs,
                    'dt_error': dt_error,
                    'content_error': content_error,
                    'v_date': date,
                    'v_time': time,
                    'v_content': content
                }
            )
        else:
            posts = {}
            for db_pc in db_pcs:
                # create one comment per post
                if db_pc.post.id not in posts.keys():
                    pc = PostComment.objects.create(
                        author=request.user,
                        content=content,
                        publishdate=dt,
                        moderated=True,
                        post=db_pc.post
                    )

                    posts[db_pc.post.id] = pc

                db_pc.response = posts[db_pc.post.id]
                db_pc.save()

            return HttpResponseRedirect('/admin/communication/postcomment/')

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def chat_response(request, cm):
    db_cm = ChatMessage.objects.filter(id=cm).first()

    if not db_cm:
        return HttpResponse("ChatMessage %s not found" % cm)

    ro = None
    response = None

    if db_cm.response:
        ro = 1
        response = db_cm.response

    def get():
        return render(
            request=request,
            template_name="misc/chat_response.html",
            dictionary={
                "cm": db_cm,
                "ro": ro,
                "response": response,
            }
        )

    def post():

        dt_error = False
        content_error = False

        dt_error, date, time, dt = validate_publish_date_and_time(request.POST)
        content_error, content = validate_content(request.POST)

        if dt_error or content_error:
            return render(
                request=request,
                template_name="misc/chat_response.html",
                dictionary={
                    "cm": db_cm,
                    "ro": ro,
                    "response": response,
                    "dt_error": dt_error,
                    "content_error": content_error,
                    "v_date": date,
                    "v_time": time,
                    "v_content": content
                }
            )
        else:
            cm = ChatMessage.objects.create(
                author=request.user,
                content=content,
                publishdate=dt,
                moderated=True,
                chatgroup=db_cm.chatgroup
            )

            db_cm.response = cm
            db_cm.save()

            return HttpResponseRedirect("/admin/communication/chatmessage/")

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def chat_response_selected(request, cm):
    cms = cm.split(',')
    db_cms = ChatMessage.objects.filter(id__in=cms, response__isnull=True)

    if db_cms.count() == 0:
        no_cms = True
    else:
        no_cms = False

    def get():

        return render(
            request=request,
            template_name='misc/chat_response_selected.html',
            dictionary={'cms': db_cms, 'no_cms': no_cms}
        )

    def post():

        dt_error = False
        content_error = False
        date = None
        time = None
        content = None

        dt_error, date, time, dt = validate_publish_date_and_time(request.POST)
        content_error, content = validate_content(request.POST)

        if dt_error or content_error:
            return render(
                request=request,
                template_name='misc/chat_response_selected.html',
                dictionary={
                    'cms': db_cms,
                    'no_cms': no_cms,
                    'dt_error': dt_error,
                    'content_error': content_error,
                    'v_date': date,
                    'v_time': time,
                    'v_content': content
                }
            )
        else:
            groups = {}
            for db_cm in db_cms:
                # create one chat message per group
                if db_cm.chatgroup.id not in groups.keys():
                    cm = ChatMessage.objects.create(
                        author=request.user,
                        content=content,
                        publishdate=dt,
                        moderated=True,
                        chatgroup=db_cm.chatgroup
                    )

                    groups[db_cm.chatgroup.id] = cm

                db_cm.response = groups[db_cm.chatgroup.id]
                db_cm.save()

            return HttpResponseRedirect('/admin/communication/chatmessage/')

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