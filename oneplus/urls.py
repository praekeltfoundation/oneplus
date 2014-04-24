from django.conf.urls import url
from oneplus import views


urlpatterns = [
    # Auth
    url(r"^$", views.login, name="auth.login"),
    url(r"^login$", views.login, name="auth.login"),
    url(r"^smspassword/(?P<msisdn>\d+)$", views.smspassword, name="auth.smspassword"),
    url(r"^getconnected$", views.getconnected, name="auth.getconnected"),

    # Learn
    url(r"^welcome$", views.welcome, name="learn.welcome"),
    url(r"^next$", views.nextchallenge, name="learn.next"),
    url(r"^right$", views.right, name="learn.right"),
    url(r"^wrong$", views.wrong, name="learn.wrong"),
    url(r"^discuss$", views.discuss, name="learn.discuss"),

    # Communicate
    url(r"^inbox$", views.inbox, name="com.inbox"),
    url(r"^inbox/(?P<messageid>\d+)$", views.inbox, name="com.inbox.id"),
    url(r"^inbox/new$", views.inbox, name="com.inbox.new"),

    url(r"^chat$", views.chat, name="com.chat"),
    url(r"^chat/(?P<chatid>\d+)$", views.chat, name="com.chat.id"),
    url(r"^chat/(?P<chatid>\d+)/new$", views.chat, name="com.chat.new"),

    url(r"^blog$", views.blog, name="com.blog"),
    url(r"^blog/(?P<blogid>\d+)$", views.blog, name="com.blog.id"),

    # Progress
    url(r"^ontrack$", views.ontrack, name="prog.ontrack"),
    url(r"^leader$", views.leader, name="prog.leader"),
    url(r"^leader/(?P<areaid>\d+)$", views.leader, name="prog.leader.id"),
    url(r"^badges$", views.badges, name="prog.badges"),

    # Misc
    url(r"^about$", views.about, name="misc.about"),
    url(r"^contact$", views.contact, name="misc.contact"),
    url(r"^investec$", views.investec, name="misc.investec"),
    url(r"^preakelt$", views.preakelt, name="misc.preakelt"),
]
