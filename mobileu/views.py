from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import user_passes_test
from communication.models import PostComment, ChatMessage, Discussion


@user_passes_test(lambda u: u.is_staff)
def publish_postcomment(request, pk):
    pc = PostComment.objects.filter(pk=pk)
    msg = ''
    err_msg = 'PostComment has not been published. Reason: '
    if pc:
        pc.moderate()
        msg = 'PostComment has been published'
    else:
        msg = '%s%s' % (err_msg, 'Can''t find record.')

    return HttpResponse(msg)

@user_passes_test(lambda u: u.is_staff)
def unpublish_postcomment(request, pk):
    pc = PostComment.objects.filter(pk=pk)
    msg = ''
    err_msg = 'PostComment has not been unpublished. Reason: '
    if pc:
        pc.update(moderated=True)
        msg = 'PostComment has been unpublished'
    else:
        msg = '%s%s' % (err_msg, 'Can''t find record.')

    return HttpResponse(msg)

@user_passes_test(lambda u: u.is_staff)
def publish_chatmessage(request, pk):
    pc = ChatMessage.objects.filter(pk=pk)
    msg = ''
    err_msg = 'ChatMessage has not been published. Reason: '
    if pc:
        pc.update(moderated=True)
        msg = 'ChatMessage has been published'
    else:
        msg = '%s%s' % (err_msg, 'Can''t find record.')

    return HttpResponse(msg)

@user_passes_test(lambda u: u.is_staff)
def unpublish_chatmessage(request, pk):
    pc = ChatMessage.objects.filter(pk=pk)
    msg = ''
    err_msg = 'ChatMessage has not been unpublished. Reason: '
    if pc:
        pc.update(moderated=True)
        msg = 'ChatMessage has been unpublished'
    else:
        msg = '%s%s' % (err_msg, 'Can''t find record.')

    return HttpResponse(msg)

@user_passes_test(lambda u: u.is_staff)
def publish_discussion(request, pk):
    pc = Discussion.objects.filter(pk=pk)
    msg = ''
    err_msg = 'Discussion has not been published. Reason: '
    if pc:
        pc.update(moderated=True)
        msg = 'Discussion has been published'
    else:
        msg = '%s%s' % (err_msg, 'Can''t find record.')

    return HttpResponse(msg)

@user_passes_test(lambda u: u.is_staff)
def unpublish_discussion(request, pk):
    pc = Discussion.objects.filter(pk=pk)
    msg = ''
    err_msg = 'Discussion has not been unpublished. Reason: '
    if pc:
        pc.update(moderated=True)
        msg = 'Discussion has been unpublished'
    else:
        msg = '%s%s' % (err_msg, 'Can''t find record.')

    return HttpResponse(msg)