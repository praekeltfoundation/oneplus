from __future__ import division
from django.shortcuts import render, HttpResponse
from django.http import HttpResponseRedirect
from django.core.mail import mail_managers
from django.db.models import Count, Q
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from datetime import datetime
from django.utils import timezone
from communication.models import Ban, ChatGroup, ChatMessage, ChatMessageLike, CoursePostRel, Message, Post,\
    PostComment, PostCommentLike, SmsQueue, Sms
from core.models import Class, Course, Learner, Participant
from .validators import validate_content, validate_course, validate_date_and_time, validate_direction, \
    validate_message, validate_name, validate_publish_date_and_time, validate_to_class, validate_to_course, \
    validate_users
from communication.utils import report_user_post
from oneplus.views import oneplus_participant_required, oneplus_login_required, _content_profanity_check
from oneplus.auth_views import resolve_http_method

__author__ = 'herman'


@oneplus_participant_required
def inbox(request, state, user, participant):
    # get inbox messages
    _participant = participant
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
             "inbox_messages": _messages,
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
                "inbox_messages": _messages,
                "message_count": len(_messages)
            }
        )

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def inbox_detail(request, state, user, participant, messageid):
    # get inbox messages
    _participant = participant
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


@oneplus_participant_required
def inbox_send(request, state, user, participant):
    # get inbox messages
    _participant = participant
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
                # Send email to info@dig-it.me
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


@oneplus_participant_required
def chatgroups(request, state, user, participant):
    # get chat groups
    _groups = participant.classs.course.chatgroup_set.all()

    for g in _groups:
        _last_msg = g.chatmessage_set.order_by("-publishdate").first()
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


@oneplus_login_required
def chat(request, state, user, chatid):
    # get chat group
    _group = ChatGroup.objects.get(pk=chatid)
    request.session["state"]["chat_page_max"] = _group.chatmessage_set.filter(moderated=True,

                                                                              publishdate__lt=datetime.now()).count()

    _usr = Learner.objects.get(pk=user["id"])

    banned = Ban.objects.filter(banned_user=_usr, till_when__gt=datetime.now())

    if not banned:
        request.session["state"]["banned"] = False
    else:
        request.session["state"]["banned"] = True

    def retrieve_comment_objects():
        return _group.chatmessage_set.filter(moderated=True,
                                             unmoderated_date=None,
                                             publishdate__lt=datetime.now())\
            .annotate(like_count=Count('chatmessagelike__user'))

    def retrieve_popular_comment_objects():
        return retrieve_comment_objects()\
            .filter(like_count__gt=0)\
            .order_by('-like_count')

    def get():
        request.session["state"]["chat_page"] \
            = min(10, request.session["state"]["chat_page_max"])

        _messages = retrieve_comment_objects() \
            .order_by("-publishdate")[:request.session["state"]["chat_page"]]
        _popular_messages = retrieve_popular_comment_objects()[:2]

        for msg in _messages:
            msg.has_liked = ChatMessageLike.has_liked(_usr, msg)

        for msg in _popular_messages:
            msg.has_liked = ChatMessageLike.has_liked(_usr, msg)

        return render(request, "com/chat.html", {"chat_messages": _messages,
                                                 "group": _group,
                                                 "most_popular": _popular_messages,
                                                 "state": state,
                                                 "user": user})

    def post():
        # new comment created
        if "comment" in request.POST.keys() and request.POST["comment"] != "":
            _comment = request.POST["comment"]
            _message = ChatMessage(
                chatgroup=_group,
                content=_comment,
                author=_usr,
                publishdate=datetime.now(),
                moderated=True
            )

            if _content_profanity_check(_message):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _message.unmoderated_date = datetime.now()
            else:
                messages.add_message(request, messages.SUCCESS,
                                     "Thank you for your contribution. Your message will display shortly! "
                                     "If not already")

                _message.save()
            request.session["state"]["chat_page_max"] += 1
            return redirect("com.chat", chatid=chatid)

        # show more comments
        elif "page" in request.POST.keys():
            request.session["state"]["chat_page"] += 10
            if request.session["state"]["chat_page"] \
                    > request.session["state"]["chat_page_max"]:
                request.session["state"]["chat_page"] \
                    = request.session["state"]["chat_page_max"]

        elif "report" in request.POST.keys():
            msg_id = request.POST["report"]
            msg = ChatMessage.objects.filter(id=msg_id).first()
            if msg is not None:
                report_user_post(msg, _usr, 3)
                messages.warning(request, "This comment has been reported")
            return redirect("com.chat", chatid=chatid)

        elif "like" in request.POST.keys():
            message_id = request.POST["like"]
            chat_message = ChatMessage.objects.filter(id=message_id).first()
            if chat_message is not None:
                if "has_liked" in request.POST.keys():
                    ChatMessageLike.unlike(_usr, chat_message)
                else:
                    ChatMessageLike.like(_usr, chat_message)
                return redirect("com.chat", chatid=chatid)

        _messages = retrieve_comment_objects() \
            .order_by("-publishdate")[:request.session["state"]["chat_page"]]

        for msg in _messages:
            msg.like_count = ChatMessageLike.count_likes(msg)
            msg.has_liked = ChatMessageLike.has_liked(_usr, msg)

        return render(
            request,
            "com/chat.html",
            {
                "state": state,
                "user": user,
                "group": _group,
                "chat_messages": _messages
            }
        )

    return resolve_http_method(request, [get, post])


@oneplus_participant_required
def blog_hero(request, state, user, participant):
    # get blog entry
    dt = timezone.now()
    _course = participant.classs.course
    post_list = CoursePostRel.objects.filter(course=_course, post__publishdate__lt=dt)\
        .values_list('post__id', flat=True)
    request.session["state"]["blog_page_max"] = Post.objects.filter(
        id__in=post_list
    ).count()
    _posts = Post.objects.filter(
        id__in=post_list
    ).order_by("-publishdate")[:4]
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


@oneplus_participant_required
def blog_list(request, state, user, participant):
    # get blog entry
    dt = timezone.now()
    _course = participant.classs.course
    post_list = CoursePostRel.objects.filter(course=_course, post__publishdate__lt=dt)\
        .values_list('post__id', flat=True)
    request.session["state"]["blog_page_max"] \
        = Post.objects.filter(id__in=post_list).count()

    def get():
        request.session["state"]["blog_page"] \
            = min(10, request.session["state"]["blog_page_max"])
        _posts = Post.objects.filter(id__in=post_list) \
                     .order_by("-publishdate")[:request.session["state"]["blog_page"]]

        return render(request, "com/bloglist.html", {"state": state,
                                                     "user": user,
                                                     "posts": _posts})

    def post():
        # show more blogs
        if "page" in request.POST.keys():
            request.session["state"]["blog_page"] += 10
            if request.session["state"]["blog_page"] > request.session["state"]["blog_page_max"]:
                request.session["state"]["blog_page"] = request.session["state"]["blog_page_max"]

        _posts = Post.objects.filter(id__in=post_list).order_by("-publishdate")[:request.session["state"]["blog_page"]]

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


@oneplus_participant_required
def blog(request, participant, state, user, blogid):
    dt = timezone.now()
    # get blog entry
    _course = participant.classs.course
    post_list = CoursePostRel.objects.filter(course=_course,
                                             post__publishdate__lt=dt).values_list('post__id', flat=True)
    _post = Post.objects.get(pk=blogid)

    _next = Post.objects.filter(
        id__in=post_list,
        publishdate__gt=_post.publishdate
    ).exclude(id=_post.id).order_by("publishdate").first()
    _previous = Post.objects.filter(
        id__in=post_list,
        publishdate__lt=_post.publishdate
    ).exclude(id=_post.id).order_by("-publishdate").first()

    if _next is not None:
        state["blog_next"] = _next.id
    else:
        state["blog_next"] = None

    if _previous is not None:
        state["blog_previous"] = _previous.id
    else:
        state["blog_previous"] = None

    latest = Post.objects.filter(id__in=post_list).latest("publishdate")

    request.session["state"]["post_comment"] = False

    _usr = Learner.objects.get(pk=user["id"])

    banned = Ban.objects.filter(banned_user=_usr, till_when__gt=datetime.now())

    if not banned:
        request.session["state"]["banned"] = False
    else:
        request.session["state"]["banned"] = True

    allow_commenting = latest and (_post.id == latest.id)

    def retrieve_comment_objects():
        return PostComment.objects.filter(post=_post, unmoderated_date=None, moderated=True)\
            .annotate(like_count=Count('postcommentlike__user'))

    def retrieve_popular_comment_objects():
        return retrieve_comment_objects()\
            .filter(like_count__gt=0)\
            .order_by('-like_count')

    def get():
        all_messages = retrieve_comment_objects()

        request.session["state"]["post_page_max"] = all_messages.count()

        request.session["state"]["post_page"] = \
            min(5, request.session["state"]["post_page_max"])

        post_comments = all_messages.order_by("-publishdate")[:request.session["state"]["post_page"]]
        _popular_messages = retrieve_popular_comment_objects()[:2]

        for comment in post_comments:
            comment.has_liked = PostCommentLike.has_liked(_usr, comment)

        for comment in _popular_messages:
            comment.has_liked = PostCommentLike.has_liked(_usr, comment)

        return render(
            request,
            "com/blog.html",
            {
                "allow_commenting": allow_commenting,
                "most_popular": _popular_messages,
                "post": _post,
                "post_comments": post_comments,
                "state": state,
                "user": user,
            }
        )

    def post():
        post_comments = retrieve_comment_objects()

        if "comment" in request.POST.keys() and request.POST["comment"] != "":
            _comment = request.POST["comment"]

            # ensure the user is not banned before we allow them to comment
            if not _usr.is_banned():
                _post_comment = PostComment(
                    post=_post,
                    author=_usr,
                    content=_comment,
                    publishdate=datetime.now(),
                    moderated=True
                )

                if _content_profanity_check(_post_comment):
                    messages.add_message(request, messages.WARNING,
                                         "Your message may contain profanity and has been submitted for review")
                    _post_comment.unmoderated_date = datetime.now()
                else:
                    messages.add_message(request, messages.SUCCESS,
                                         "Thank you for your contribution. Your message will display shortly! "
                                         "If not already")

                _post_comment.save()

                request.session["state"]["post_comment"] = True
                return redirect('com.blog', blogid)

        elif "page" in request.POST.keys():
            request.session["state"]["post_page"] += 5
            if request.session["state"]["post_page"] > request.session["state"]["post_page_max"]:
                request.session["state"]["post_page"] = request.session["state"]["post_page_max"]

        elif "report" in request.POST.keys():
            post_id = request.POST["report"]
            post_comment = PostComment.objects.filter(id=post_id).first()
            if post_comment is not None:
                report_user_post(post_comment, _usr, 1)
            return redirect('com.blog', blogid)

        elif "like" in request.POST.keys():
            post_id = request.POST["like"]
            post_comment = PostComment.objects.filter(id=post_id).first()
            if post_comment is not None:
                if "has_liked" in request.POST.keys():
                    PostCommentLike.unlike(_usr, post_comment)
                else:
                    PostCommentLike.like(_usr, post_comment)
                return redirect("com.blog", blogid=blogid)

        post_comments = retrieve_comment_objects()

        request.session["state"]["post_page_max"] = post_comments.count()

        request.session["state"]["post_page"] = \
            min(5, request.session["state"]["post_page_max"])

        post_comments = post_comments.order_by("-publishdate")[:request.session["state"]["post_page"]]
        _popular_messages = retrieve_popular_comment_objects()[:2]

        for comment in post_comments:
            comment.has_liked = PostCommentLike.has_liked(_usr, comment)

        for comment in _popular_messages:
            comment.has_liked = PostCommentLike.has_liked(_usr, comment)

        return render(
            request,
            "com/blog.html",
            {
                "allow_commenting": allow_commenting,
                "most_popular": _popular_messages,
                "post": _post,
                "post_comments": post_comments,
                "state": state,
                "user": user,
            }
        )

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
        active_only = request.POST.get('active_only', None)

        name_error, name = validate_name(request.POST)
        course_error, course = validate_course(request.POST)
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
                    'course_error': course_error,
                    'to_class_error': class_error,
                    'users_error': users_error,
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
            if "all" in users:
                #means all users in certain class and course
                if classs == "all":
                    if course == "all":
                        #All registered learners
                        all_courses = Course.objects.all()

                        for _course in all_courses:
                            all_classes = Class.objects.filter(course=_course)

                            for _classs in all_classes:
                                all_users = Participant.objects.filter(classs=_classs)

                                for usr in all_users:
                                    create_message(name, _course, _classs, usr.learner, direction, dt, content)
                    else:
                        #All users registered in this course
                        course_obj = Course.objects.get(id=course)
                        all_classes = Class.objects.filter(course=course_obj)

                        for c in all_classes:
                            all_users = Participant.objects.filter(classs=c)

                            for u in all_users:
                                create_message(name, course_obj, c, u.learner, direction, dt, content)
                else:
                    #All learners in specific class
                    classs_obj = Class.objects.get(id=classs)
                    all_users = Participant.objects.filter(classs=classs_obj)

                    for u in all_users:
                        create_message(name, classs_obj.course, classs_obj, u.learner, direction, dt, content)
            else:
                #Specific learners
                for u in users:
                    usr = Learner.objects.get(id=u)
                    _participant = Participant.objects.filter(learner=usr, is_active=True).first()
                    create_message(name, _participant.classs.course, _participant.classs, usr, direction, dt, content)

        if "_save" in request.POST.keys():
            return HttpResponseRedirect('/admin/communication/message/')
        else:
            return HttpResponseRedirect('/message/add')

    def create_message(name, course, classs, user, direction, publishdate, content):
        Message.objects.create(
            name=name,
            course=course,
            to_class=classs,
            to_user=user,
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
def add_sms(request):
    def get():
        return render(
            request=request,
            template_name='misc/queued_sms.html',
        )

    def post():
        course_error = False
        class_error = False
        dt_error = False
        message_error = False
        users_error = False

        course = None
        classs = None
        date = None
        time = None
        message = None
        users = False
        active_only = request.POST.get('active_only', None)

        course_error, course = validate_to_course(request.POST)
        class_error, classs = validate_to_class(request.POST)
        dt_error, date, time, dt = validate_date_and_time(request.POST)
        message_error, message = validate_message(request.POST)
        users_error, users = validate_users(request.POST)

        if course_error or class_error or dt_error or message_error or users_error:
            return render(
                request=request,
                template_name='misc/queued_sms.html',
                dictionary={
                    'to_course_error': course_error,
                    'to_class_error': class_error,
                    'users_error': users_error,
                    'dt_error': dt_error,
                    'message_error': message_error,
                    'v_date': date,
                    'v_time': time,
                    'v_message': message,
                }
            )

        else:
            if "all" in users:
                #means all users in certain class and course
                if classs == "all":
                    if course == "all":
                        #All registered learners
                        all_users = Learner.objects.filter(is_active=True)\
                                                   .exclude(Q(participant__classs=None) |
                                                            Q(participant__classs__course=None))
                        if active_only:
                            all_users.filter(participant__is_active=True)
                        if all_users.exists():
                            bulk_create_sms(all_users, dt, message)
                    else:
                        #All users registered in this course
                        course_obj = Course.objects.get(id=course)
                        all_users = Learner.objects.filter(participant__classs__course_id=course_obj)\
                            .exclude(participant__classs=None)
                        if active_only:
                            all_users.filter(participant__is_active=True)
                        if all_users.exists():
                            bulk_create_sms(all_users, dt, message)
                else:
                    #All learners in specific class
                    classs_obj = Class.objects.get(id=classs)
                    all_users = Learner.objects.filter(participant__classs_id=classs_obj.id)
                    if active_only:
                        all_users.filter(participant__is_active=True)
                    if all_users.exists():
                        bulk_create_sms(all_users, dt, message)
            else:
                #Specific learners
                all_users = Learner.objects.filter(id__in=users)
                if all_users.exists():
                    bulk_create_sms(all_users, dt, message)

        if "_save" in request.POST.keys():
            return HttpResponseRedirect('/admin/communication/smsqueue/')
        else:
            return HttpResponseRedirect('/smsqueue/add/')

    def bulk_create_sms(learners, send_date, message):
        SmsQueue.objects.bulk_create([
            SmsQueue(
                msisdn=l.mobile,
                send_date=send_date,
                message=message
            ) for l in learners])

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def view_sms(request, sms):
    db_sms = SmsQueue.objects.filter(id=sms).first()

    if db_sms is None:
        return HttpResponse("Queued SMS not found")

    def get():
        return render(
            request=request,
            template_name='misc/queued_sms.html',
            dictionary={
                'sms': db_sms,
                'ro': True
            }
        )

    def post():
        return render(
            request=request,
            template_name='misc/queued_sms.html',
            dictionary={
                'sms': db_sms,
                'ro': True
            }
        )

    return resolve_http_method(request, [get, post])


@user_passes_test(lambda u: u.is_staff)
def sms_response(request, sms):
    db_sms = Sms.objects.filter(id=sms).first()

    if db_sms:
        db_participant = Participant.objects.filter(learner__mobile__contains=db_sms.msisdn).first()

    else:
        return HttpResponse("Sms %s not found" % sms)

    ro = None
    resp = None

    if db_sms.response:
        ro = 1
        resp = db_sms.response

    def get():

        return render(
            request=request,
            template_name="misc/sms_response.html",
            dictionary={"sms": db_sms, "participant": db_participant, "ro": ro, "response": resp}
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
                template_name="misc/sms_response.html",
                dictionary={
                    "sms": db_sms,
                    "participant": db_participant,
                    "ro": ro,
                    "response": resp,
                    "dt_error": dt_error,
                    "content_error": content_error,
                    "v_date": date,
                    "v_time": time,
                    "v_content": content
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

            return HttpResponseRedirect("/admin/communication/sms/")

    return resolve_http_method(request, [get, post])
