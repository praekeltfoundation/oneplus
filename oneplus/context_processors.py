def social_media(request):
    from django.conf import settings
    return {
        'FB_APP_NUM': settings.FB_APP_NUM,
        'FB_REDIRECT': settings.FB_REDIRECT,
        'FB_SITE_TITLE': settings.FB_SITE_TITLE,
        'FB_SITE_DESC': settings.FB_SITE_DESC,
    }
