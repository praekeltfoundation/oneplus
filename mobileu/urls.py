from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mobileu.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    (r"^summernote/", include("django_summernote.urls")),
    url(r'^oneplus/', include('oneplus.urls')),
    url(r'^admin/', include(admin.site.urls))
)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()

