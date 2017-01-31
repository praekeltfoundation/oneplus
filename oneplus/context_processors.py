def social_media(request):
    from django.conf import settings
    return {
        'FB_APP_NUM': settings.FB_APP_NUM,
        'FB_REDIRECT': settings.FB_REDIRECT,
    }
