from django.conf.urls import url
from core import views


urlpatterns = [
    url(r"^$", views.index, name="index"),
    url(r"^school/(?P<school_id>\d+)", views.school_detail, name="school.detail"),
    url(r"^school/", views.school_list, name="school.list")

]