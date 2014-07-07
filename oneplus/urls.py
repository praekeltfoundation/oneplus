from django.conf.urls import url, include
from oneplus import views
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    # Misc
    url(r"^$", views.welcome, name="misc.welcome"),
    url(r"^about$", views.about, name="misc.about"),
    url(r"^contact$", views.contact, name="misc.contact"),
    url(r"^menu$", views.menu, name="core.menu"),

    # Auth
    url(r"^login$", views.login, name="auth.login"),
    url(r"^signout$", views.signout, name="auth.signout"),
    url(r"^smspassword$",
        views.smspassword,
        name="auth.smspassword"),
    url(r"^getconnected$", views.getconnected, name="auth.getconnected"),
    url(r"^autologin/(?P<token>\S+)$", views.autologin, name="auth.autologin"),

    # Learn
    url(r"^home", views.home, name="learn.home"),
    url(r"^next$", views.nextchallenge, name="learn.next"),
    url(r"^right$", views.right, name="learn.right"),
    url(r"^wrong$", views.wrong, name="learn.wrong"),
    url(r"^discuss$", views.discuss, name="learn.discuss"),
    url(r"^preview/(?P<questionid>\d+)$",
        views.adminpreview,
        name="learn.preview"),
    url(r"^preview/right/(?P<questionid>\d+)$",
        views.adminpreview_right,
        name="learn.preview.right"),
    url(r"^preview/wrong/(?P<questionid>\d+)$",
        views.adminpreview_wrong,
        name="learn.preview.wrong"),

    # Communicate
    url(r"^inbox$", views.inbox, name="com.inbox"),
    url(r"^inbox/(?P<messageid>\d+)$",
        views.inbox_detail,
        name="com.inbox_detail"),
    url(r"^inbox_send", views.inbox_send, name="com.inbox_send"),

    url(r"^chat$", views.chatgroups, name="com.chatgroups"),
    url(r"^chat/(?P<chatid>\d+)$", views.chat, name="com.chat"),

    url(r"^blog$", views.blog_hero, name="com.bloghero"),
    url(r"^bloglist$", views.blog_list, name="com.bloglist"),
    url(r"^blog/(?P<blogid>\d+)$", views.blog, name="com.blog"),

    # Progress
    url(r"^ontrack$", views.ontrack, name="prog.ontrack"),
    url(r"^leader$", views.leader, name="prog.leader"),
    url(r"^points$", views.points, name="prog.points"),
    url(r"^leader/(?P<areaid>\d+)$",
        views.leader,
        name="prog.leader.id"),
    url(r"^badges$", views.badges, name="prog.badges"),
    url(r'^djga/', include('google_analytics.urls')),
]