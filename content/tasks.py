from djcelery import celery
from content.forms import render_mathml


@celery.task
def render_mathml_content():
    render_mathml()