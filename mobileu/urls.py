from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from . import views

admin.autodiscover()

urlpatterns = \
    patterns('',
             (r"^summernote/", include("django_summernote.urls")),
             (r'^grappelli/', include('grappelli.urls')),
             url(r'^admin/', include(admin.site.urls)),
             url(
                 r'^admin/communication/postcomment/publish/(?P<pk>\d+)$',
                 views.publish_postcomment,
                 name='pub.postcomment'
             ),
             url(
                 r'^admin/communication/postcomment/unpublish/(?P<pk>\d+)$',
                 views.unpublish_postcomment,
                 name='unpub.postcomment'
             ),
             url(
                 r'^admin/communication/chatmessage/publish/(?P<pk>\d+)$',
                 views.publish_chatmessage,
                 name='pub.chatmessage'
             ),
             url(
                 r'^admin/communication/chatmessage/unpublish/(?P<pk>\d+)$',
                 views.unpublish_chatmessage,
                 name='unpub.chatmessage'
             ),
             url(
                 r'^admin/communication/discussion/publish/(?P<pk>\d+)$',
                 views.publish_discussion,
                 name='pub.discussion'
             ),
             url(
                 r'^admin/communication/discussion/unpublish/(?P<pk>\d+)$',
                 views.unpublish_discussion,
                 name='unpub.discussion'
             ),
             ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
