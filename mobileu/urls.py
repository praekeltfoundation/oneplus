from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mobileu.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    (r"^summernote/", include("django_summernote.urls")),
    url(r'^oneplus/', include('oneplus.urls')),
    url(r'^admin/', include(admin.site.urls))
)
