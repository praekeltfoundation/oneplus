from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from core.models import *


def index(request):
    return HttpResponse("Hello, world. You're at the organisations index.")


def school_list(request):
    return render(request, "school/list.html", { "allschools": School.objects.all() })


def school_detail(request, school_id):
    school = get_object_or_404(School, pk=school_id)
    return render(request, "school/detail.html", {"school": school})

