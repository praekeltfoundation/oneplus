from django.conf.urls import url, include
from oneplus import views
import oneplus.auth_views
import oneplus.com_views
import oneplus.core_views
import oneplus.learn_views
import oneplus.misc_views
import oneplus.prog_views
from oneplus import result_views

urlpatterns = [
    # Misc
    url(r"^$", oneplus.misc_views.welcome, name="misc.welcome"),
    url(r"^about$", oneplus.misc_views.about, name="misc.about"),
    url(r"^contact$", oneplus.misc_views.contact, name="misc.contact"),
    url(r"^menu$", oneplus.core_views.menu, name="core.menu"),
    url(r"^faq$", oneplus.misc_views.faq, name="misc.faq"),
    url(r'^terms$', oneplus.misc_views.terms, name="misc.terms"),

    # Auth
    url(r"^login$", oneplus.auth_views.login, name="auth.login"),
    url(r"^signout$", oneplus.auth_views.signout, name="auth.signout"),
    url(r"^smspassword$",
        oneplus.auth_views.smspassword,
        name="auth.smspassword"),
    url(r"^getconnected$", oneplus.auth_views.getconnected, name="auth.getconnected"),
    url(r"^a/(?P<token>\S+)$", oneplus.auth_views.autologin, name="auth.autologin"),
    url(r'^signup$', oneplus.auth_views.signup, name="auth.signup"),
    url(r'^signup_form$', oneplus.auth_views.signup_form, name="auth.signup_form"),
    url(r'^signup_form_promath$', oneplus.auth_views.signup_form_promath, name="auth.signup_form_promath"),
    url(r'^changedetails$', oneplus.auth_views.change_details, name="auth.change_details"),

    # Learn
    url(r"^home", oneplus.learn_views.home, name="learn.home"),
    url(r"^next$", oneplus.learn_views.nextchallenge, name="learn.next"),
    url(r"^right$", oneplus.learn_views.right, name="learn.right"),
    url(r"^wrong$", oneplus.learn_views.wrong, name="learn.wrong"),
    url(r"^event$", oneplus.learn_views.event, name="learn.event"),
    url(r"^event_right$", oneplus.learn_views.event_right, name="learn.event_right"),
    url(r"^event_wrong$", oneplus.learn_views.event_wrong, name="learn.event_wrong"),
    url(r"^preview/(?P<questionid>\d+)$",
        oneplus.learn_views.adminpreview,
        name="learn.preview"),
    url(r"^preview/right/(?P<questionid>\d+)$",
        oneplus.learn_views.adminpreview_right,
        name="learn.preview.right"),
    url(r"^preview/wrong/(?P<questionid>\d+)$",
        oneplus.learn_views.adminpreview_wrong,
        name="learn.preview.wrong"),
    url(r"^welcome$", oneplus.misc_views.first_time, name="learn.first_time"),
    url(r"^report_question/(?P<questionid>\d+)/(?P<frm>\w{0,5})$", oneplus.learn_views.report_question, name="learn.report_question"),
    url(r"^event_splash_page", oneplus.learn_views.event_splash_page, name="learn.event_splash_page"),
    url(r"^event_start_page", oneplus.learn_views.event_start_page, name="learn.event_start_page"),
    url(r"^event_end_page", oneplus.learn_views.event_end_page, name="learn.event_end_page"),

    # Communicate
    url(r"^inbox$", oneplus.com_views.inbox, name="com.inbox"),
    url(r"^inbox/(?P<messageid>\d+)$",
        oneplus.com_views.inbox_detail,
        name="com.inbox_detail"),
    url(r"^inbox_send", oneplus.com_views.inbox_send, name="com.inbox_send"),

    url(r"^chat$", oneplus.com_views.chatgroups, name="com.chatgroups"),
    url(r"^chat/(?P<chatid>\d+)$", oneplus.com_views.chat, name="com.chat"),

    url(r"^blog$", oneplus.com_views.blog_hero, name="com.bloghero"),
    url(r"^bloglist$", oneplus.com_views.blog_list, name="com.bloglist"),
    url(r"^blog/(?P<blogid>\d+)$", oneplus.com_views.blog, name="com.blog"),

    url(r"^report_response/(?P<report>\d+)$",
        oneplus.misc_views.report_response,
        name="com.represp"),
    url(r"^message_response/(?P<msg>\d+)$",
        oneplus.misc_views.message_response,
        name="com.msgresp"),
    url(r"^discussion_response/(?P<disc>\d+)$",
        oneplus.misc_views.discussion_response,
        name="com.discresp"),
    url(r"^sms_response/(?P<sms>\d+)$",
        oneplus.com_views.sms_response,
        name="com.smsresp"),
    url(r"^smsqueue/add/$", oneplus.com_views.add_sms, name="com.add_sms"),
    url(r"^smsqueue/(?P<sms>\d+)/$", oneplus.com_views.view_sms, name="com.view_sms"),
    url(r"^discussion_response_selected/(?P<disc>(\d+)(,\s*\d+)*)$",
        oneplus.misc_views.discussion_response_selected,
        name="com.discrespsel"),

    url(r"^blog_comment_response/(?P<pc>\d+)$",
        oneplus.misc_views.blog_comment_response,
        name="com.blogcomresp"),
    url(r"^blog_comment_response_selected/(?P<pc>(\d+)(,\s*\d+)*)$",
        oneplus.misc_views.blog_comment_response_selected,
        name="com.blogcomrespsel"),

    url(r"^chat_response/(?P<cm>\d+)$",
        oneplus.misc_views.chat_response,
        name="com.chatresp"),
    url(r"^chat_response_selected/(?P<cm>(\d+)(,\s*\d+)*)$",
        oneplus.misc_views.chat_response_selected,
        name="com.chatrespsel"),

    url(r"^message/add/$", oneplus.com_views.add_message, name="com.add_message"),
    url(r"^message/(?P<msg>\d+)/$", oneplus.com_views.view_message, name="com.view_message"),

    # Progress
    url(r"^ontrack$", oneplus.prog_views.ontrack, name="prog.ontrack"),
    url(r"^leader$", oneplus.prog_views.leader, name="prog.leader"),
    url(r"^points$", oneplus.prog_views.points, name="prog.points"),
    url(r"^leader/(?P<areaid>\d+)$",
        oneplus.prog_views.leader,
        name="prog.leader.id"),
    url(r"^badges$", oneplus.prog_views.badges, name="prog.badges"),
    url(r'^djga/', include('google_analytics.urls')),

    # Dashboard
    url(r'^dashboard_data$', oneplus.misc_views.dashboard_data, name="dash.data"),
    url(r'^dashboard$', oneplus.misc_views.dashboard, name='dash.board'),

    # Reports
    url(r'^reports$', oneplus.misc_views.reports, name='reports.home'),
    url(r'^report_learner_report/(?P<mode>\d+)/(?P<region>\w*)$',
        oneplus.misc_views.report_learner,
        name="reports.learner"),
    url(r'^reports_learner_unique_regions$',
        oneplus.misc_views.reports_learner_unique_regions,
        name="reports.unique_regions"),
    url(r'^report_question_difficulty_report/(?P<mode>\d+)$',
        views.question_difficulty_report,
        name='reports.question_difficulty'),

    #filtering for message admin
    url(r'^courses$', views.get_courses),
    url(r'^classes/(?P<course>\w+)$', views.get_classes),
    url(r'^users/(?P<classs>\w+)$', views.get_users),

    url(r"^admin/results/(?P<course>\d+)$",
        result_views.ResultsView.as_view(),
        name="results.home"),
]
