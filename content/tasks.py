from mobileu.celery import app
from content.forms import render_mathml


@app.tasks
def render_mathml_content():
    render_mathml()