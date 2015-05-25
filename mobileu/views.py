from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import user_passes_test
from communication.models import PostComment, ChatMessage, Discussion
from communication.utils import moderate, unmoderate, ban_user
from auth.models import CustomUser


def _publish(obj, name):
    msg = ''
    err_msg = '%s has not been published. Reason: ' % name
    if obj:
        try:
            moderate(obj)
            msg = '%s has been published' % name
        except Exception as ex:
            msg = '%s%s' % (err_msg, ex.message)
    else:
        msg = '%s%s' % (err_msg, 'Can''t find record.')

    return msg


def _unpublish(obj, name, user):
    msg = ''
    err_msg = '%s has not been unpublished. Reason: ' % name
    if obj:
        try:
            unmoderate(obj, user)

            if user.is_staff:
                num_ban_days = 3
            else:
                num_ban_days = 1

            ban_user(obj.author, user, obj, num_ban_days)
            msg = '%s has been unpublished' % name
        except Exception as ex:
            msg = '%s%s' % (err_msg, ex.message)
    else:
        msg = '%s%s' % (err_msg, 'Can''t find record.')

    return msg


@user_passes_test(lambda u: u.is_staff)
def publish_postcomment(request, pk):
    pc = PostComment.objects.filter(pk=pk).first()
    return HttpResponse(_publish(pc, 'PostComment'))


@user_passes_test(lambda u: u.is_staff)
def unpublish_postcomment(request, pk):
    pc = PostComment.objects.filter(pk=pk).first()
    return HttpResponse(_unpublish(pc, 'PostComment', request.user))


@user_passes_test(lambda u: u.is_staff)
def publish_chatmessage(request, pk):
    cm = ChatMessage.objects.filter(pk=pk).first()
    return HttpResponse(_publish(cm, 'ChatMessage'))


@user_passes_test(lambda u: u.is_staff)
def unpublish_chatmessage(request, pk):
    cm = ChatMessage.objects.filter(pk=pk).first()
    return HttpResponse(_unpublish(cm, 'ChatMessage', request.user))


@user_passes_test(lambda u: u.is_staff)
def publish_discussion(request, pk):
    d = Discussion.objects.filter(pk=pk).first()
    return HttpResponse(_publish(d, 'Discussion'))


@user_passes_test(lambda u: u.is_staff)
def unpublish_discussion(request, pk):
    d = Discussion.objects.filter(pk=pk).first()
    return HttpResponse(_unpublish(d, 'Discussion', request.user))