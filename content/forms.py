import re
import uuid
import os
import shutil

from django import forms
from content.models import TestingQuestion, TestingQuestionOption, Module, Mathml, GoldenEgg
import requests
from django.conf import settings
from core.models import Class
from organisation.models import Course


class TestingQuestionCreateForm(forms.ModelForm):
    module = forms.ModelChoiceField(queryset=Module.objects.all(),
                                    error_messages={'required': 'A Test question needs to '
                                                                'be associated with a module.'})

    def save(self, commit=True):
        testing_question = super(TestingQuestionCreateForm, self).save(commit=False)

        testing_question.save()

        question_content = self.cleaned_data.get("question_content")
        testing_question.question_content = process_mathml_content(question_content, 0, testing_question.id)

        answer_content = self.cleaned_data.get("answer_content")
        testing_question.answer_content = process_mathml_content(answer_content, 1, testing_question.id)

        testing_question.save()

        return testing_question

    class Meta:
        model = TestingQuestion


class TestingQuestionOptionCreateForm(forms.ModelForm):
    def save(self, commit=True):
        question_option = super(TestingQuestionOptionCreateForm, self).save(commit=False)

        question_option.save()

        option_content = self.cleaned_data.get("content")
        question_option.content = process_mathml_content(option_content, 2, question_option.id)

        question_option.save()

        return question_option

    class Meta:
        model = TestingQuestionOption


class TestingQuestionFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(TestingQuestionFormSet, self).__init__(*args, **kwargs)
        self.initial = [{'order': '1'}, {'order': '2'}]

    def clean(self):
        super(TestingQuestionFormSet, self).clean()

        question_options = []
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            data = form.cleaned_data
            question_options.append(data.get('correct'))

        if len(question_options) < 2:
            raise forms.ValidationError({'name': ['A minimum of 2 question options must be added.', ]})

        correct_selected = False
        for qo in question_options:
            if qo is True:
                correct_selected = True
                break

        if correct_selected is False:
            raise forms.ValidationError({'correct': ['One correct answer is required.', ]})


def process_mathml_content(_content, _source, _source_id):
    _content = convert_to_tags(_content)

    mathml = re.findall("<math.*?>.*?</math>", _content)

    for m in mathml:
        _content = re.sub("<math.*?>.*?</math>", process_mathml_tag(m, _source, _source_id), _content, count=1)

    return _content


def process_mathml_tag(_content, _source, _source_id):
    image_format = 'PNG'

    directory = settings.MEDIA_ROOT

    # if not os.path.exists(directory):
    # os.makedirs(directory)

    unique_filename = str(uuid.uuid4()) + '.' + image_format.lower()

    while True:
        if not os.path.isfile(directory + unique_filename):
            break
        else:
            unique_filename = str(uuid.uuid4()) + '.' + image_format.lower()

    # coming soon image that will be displayed until the mathml content is rendered
    temp_image = "%s/being_rendered.png" % settings.MEDIA_ROOT

    # copy temp image to a mathml folder with unique name
    if os.path.isfile(temp_image):
        shutil.copyfile(temp_image, directory + unique_filename)

    Mathml.objects.create(mathml_content=convert_to_text(_content),
                          filename=unique_filename,
                          source=_source,
                          source_id=_source_id,
                          rendered=False)

    return "<img src='/media/%s'/>" % unique_filename


def convert_to_tags(_content):
    codes = (('>', '&gt;'),
             ('<', '&lt;'))

    for code in codes:
        _content = _content.replace(code[1], code[0])

    return _content


def convert_to_text(_content):
    codes = (('&gt;', '>'),
             ('&lt;', '<'))

    for code in codes:
        _content = _content.replace(code[1], code[0])

    return _content


def render_mathml():
    url = settings.MATHML_URL
    max_size = 200
    image_format = 'PNG'
    quality = 1
    directory = settings.MEDIA_ROOT


    # get all the mathml objects that have not been rendered
    not_rendered = Mathml.objects.filter(rendered=False)

    for nr in not_rendered:
        # 0 - question 1 - answer
        if nr.source == 0 or nr.source == 1:
            # check if the source still exists (testing question)
            if TestingQuestion.objects.filter(id=nr.source_id).count() == 0:
                # delete image and record as the source doesn't exists anymore
                if os.path.isfile(directory + nr.filename):
                    os.remove(directory + nr.filename)
                nr.delete()
                continue
        else:
            # else is 2 - option
            if TestingQuestionOption.objects.filter(id=nr.source_id).count() == 0:
                if os.path.isfile(directory + nr.filename):
                    os.remove(directory + nr.filename)
                nr.delete()
                continue

        # get the mathml content
        content = nr.mathml_content

        values = {'mathml': content,
                  'max_size': max_size,
                  'image_format': image_format,
                  'quality': quality}

        # request mathml to be processed into an image
        r = requests.post(url, data=values, stream=True)

        # if successful replace the image
        if r.status_code == 200:
            if not os.path.exists(directory):
                os.makedirs(directory)

            unique_filename = nr.filename

            # file exists remove it
            if os.path.isfile(directory + unique_filename):
                os.remove(directory + unique_filename)

            # save the new rendered image with the right filename
            with open(directory + unique_filename, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)

            nr.rendered = True
            nr.error = ""
            nr.save()
        else:
            nr.error = r.text
            nr.save()


class GoldenEggCreateForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.all())

    def clean_classs(self):
        course = self.data.get("course")
        print course
        classs = self.cleaned_data.get("classs")
        print classs
        active = self.data.get("active") == "on"
        active_golden_eggs_class = GoldenEgg.objects.filter(classs=classs, active=True)
        print active_golden_eggs_class
        active_golden_eggs_course = GoldenEgg.objects.filter(course=course, classs=None, active=True)
        print active_golden_eggs_course
        if (active_golden_eggs_class.exists() or active_golden_eggs_course.exists()) and active:
            raise forms.ValidationError("There can only be one active Golden Egg per class")
        if active_golden_eggs_course.exists() and active:
            raise forms.ValidationError("There can only be one active Golden Egg per class")
        if active_golden_eggs_class.exists() and active:
            raise forms.ValidationError("There can only be one active Golden Egg per class")
        return classs

    def clean_point_value(self):
        points = self.data["point_value"]
        airtime = self.data["airtime"]
        badge = self.data["badge"]
        if points is None and airtime is None and not badge:
            raise forms.ValidationError("One reward must be selected")
        if points and (airtime or badge):
            raise forms.ValidationError("Only one reward can be applied")
        if points:
            return points
        return None

    def clean_airtime(self):
        points = self.data["point_value"]
        airtime = self.data["airtime"]
        badge = self.data["badge"]
        if points is None and airtime is None and not badge:
            raise forms.ValidationError("One reward must be selected")
        if airtime and (points or badge):
            raise forms.ValidationError("Only one reward can be applied")
        if airtime:
            return airtime
        return None

    def clean_badge(self):
        points = self.data["point_value"]
        airtime = self.data["airtime"]
        badge = self.data["badge"]
        if points is None and airtime is None and not badge:
            raise forms.ValidationError("One reward must be selected")
        if badge and (points or airtime):
            raise forms.ValidationError("Only one reward can be applied")
        if badge:
            return self.cleaned_data.get("badge")
        return None

    class Meta:
        model = GoldenEgg
