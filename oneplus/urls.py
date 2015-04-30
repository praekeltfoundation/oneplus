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
    url(r"^faq$", views.faq, name="misc.faq"),
    url(r'^terms$', views.terms, name="misc.terms"),

    # Auth
    url(r"^login$", views.login, name="auth.login"),
    url(r"^signout$", views.signout, name="auth.signout"),
    url(r"^smspassword$",
        views.smspassword,
        name="auth.smspassword"),
    url(r"^getconnected$", views.getconnected, name="auth.getconnected"),
    url(r"^a/(?P<token>\S+)$", views.autologin, name="auth.autologin"),
    url(r'^signup$', views.signup, name="auth.signup"),
    url(r'signup/form', views.signup_form, name="auth.signup_form"),

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
    url(r"^welcome$", views.first_time, name="learn.first_time"),
    url(r"^report_question/(?P<questionid>\d+)/(?P<frm>\w{0,5})$", views.report_question, name="learn.report_question"),

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

    url(r"^report_response/(?P<report>\d+)$",
        views.report_response,
        name="com.represp"),
    url(r"^message_response/(?P<msg>\d+)$",
        views.message_response,
        name="com.msgresp"),
    url(r"^discussion_response/(?P<disc>\d+)$",
        views.discussion_response,
        name="com.discresp"),
    url(r"^sms_response/(?P<sms>\d+)$",
        views.sms_response,
        name="com.smsresp"),
    url(r"^smsqueue/add/$", views.add_sms, name="com.add_sms"),
    url(r"^smsqueue/(?P<sms>\d+)/$", views.view_sms, name="com.view_sms"),
    url(r"^discussion_response_selected/(?P<disc>(\d+)(,\s*\d+)*)$",
        views.discussion_response_selected,
        name="com.discrespsel"),

    url(r"^message/add/$", views.add_message, name="com.add_message"),
    url(r"^message/(?P<msg>\d+)/$", views.view_message, name="com.view_message"),

    # Progress
    url(r"^ontrack$", views.ontrack, name="prog.ontrack"),
    url(r"^leader$", views.leader, name="prog.leader"),
    url(r"^points$", views.points, name="prog.points"),
    url(r"^leader/(?P<areaid>\d+)$",
        views.leader,
        name="prog.leader.id"),
    url(r"^badges$", views.badges, name="prog.badges"),
    url(r'^djga/', include('google_analytics.urls')),

    # Dashboard
    url(r'^dashboard_data$', views.dashboard_data, name="dash.data"),
    url(r'^dashboard$', views.dashboard, name='dash.board'),

    # Reports
    url(r'^reports$', views.reports, name='reports.home'),
    url(r'^report_learner_report/(?P<mode>\d+)/(?P<region>\w*)$',
        views.report_learner,
        name="reports.learner"),
    url(r'^reports_learner_unique_regions$',
        views.reports_learner_unique_regions,
        name="reports.unique_regions"),
    url(r'^report_question_difficulty_report/(?P<mode>\d+)$',
        views.question_difficulty_report,
        name='reports.question_difficulty'),

    #filtering for message admin
    url(r'^courses$', views.get_courses),
    url(r'^classes/(?P<course>\w+)$', views.get_classes),
    url(r'^users/(?P<classs>\w+)$', views.get_users),
]
