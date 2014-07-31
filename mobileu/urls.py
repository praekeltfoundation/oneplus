from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

admin.autodiscover()

urlpatterns = \
    patterns('',
             (r"^summernote/", include("django_summernote.urls")),
             (r'^grappelli/', include('grappelli.urls')),
             url(r'^admin/', include(admin.site.urls))
             ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
