import re
import uuid
import os
import shutil
import logging
import requests

from django import forms
from content.models import TestingQuestion, TestingQuestionOption, Module, Mathml, GoldenEgg, Event, SUMitEndPage,\
    TestingQuestionDifficulty
from django.conf import settings
from django.db.models import Max
from core.models import Class
from organisation.models import Course
from datetime import datetime

# Get an instance of a logger
logger = logging.getLogger(__name__)


class TestingQuestionCreateForm(forms.ModelForm):
    module = forms.ModelChoiceField(queryset=Module.objects.all(),
                                    error_messages={'required': 'A Test question needs to '
                                                                'be associated with a module.'})

    def clean_name(self):
        name = self.data.get("name")
        if name == "Auto Generated":
            module = self.data.get("module")
            if not module:
                raise forms.ValidationError("You must select a module")
            count = TestingQuestion.objects.filter(module__id=module).count() + 1
            module = Module.objects.get(id=module)
            self.data["name"] = "%s Question %d" % (module, count)
            return "%s Question %d" % (module, count)
        return name

    def clean_order(self):
        order = self.data.get("order")
        if order == 0:
            module = self.data.get("module")
            if not module:
                raise forms.ValidationError("You must select a module")
            count = TestingQuestion.objects.filter(module__id=module).count() + 1
            return count
        return order

    def save(self, commit=True):
        testing_question = super(TestingQuestionCreateForm, self).save(commit=False)
        if testing_question.order == 0 or testing_question.name == "Auto Generated":
            count = TestingQuestion.objects.filter(module__id=self.data.get("module")).count() + 1
            module = Module.objects.get(id=self.data.get("module"))
            name = "%s Question %d" % (module, count)
            while TestingQuestion.objects.filter(name=name):
                count += 1
                name = "%s Question %d" % (module, count)
            testing_question.name = name
            testing_question.order = count
        testing_question.save()

        question_content = self.cleaned_data.get("question_content")
        testing_question.question_content = process_mathml_content(
            question_content,
            Mathml.TESTING_QUESTION_QUESTION,
            testing_question.id
        )

        answer_content = self.cleaned_data.get("answer_content")
        testing_question.answer_content = process_mathml_content(
            answer_content,
            Mathml.TESTING_QUESTION_ANSWER,
            testing_question.id
        )

        notes = self.cleaned_data.get("notes")
        testing_question.notes = process_mathml_content(
            notes,
            Mathml.TESTING_QUESTION_NOTES,
            testing_question.id
        )

        if testing_question.difficulty != TestingQuestion.DIFF_NONE:
            points = TestingQuestionDifficulty.objects.get(key=testing_question.difficulty).value
            testing_question.points = points

        testing_question.save()

        return testing_question

    class Meta:
        model = TestingQuestion


class TestingQuestionOptionCreateForm(forms.ModelForm):
    def clean_name(self):
        question = self.data.get("question")
        if not question:
            raise ValueError("Question must be selected")
        question = TestingQuestion.objects.get(id=self.data.get("question"))
        order = self.data.get("order")
        if not order:
            raise ValueError("Order must be filled in")
        return "%s Option %s" % (question, order)

    def save(self, commit=True):
        question_option = super(TestingQuestionOptionCreateForm, self).save(commit=False)
        question = TestingQuestion.objects.get(id=self.data.get("question"))
        order = TestingQuestionOption.objects.filter(question=question).count() + 1
        question_option.order = order
        question_option.name = "%s Option %s" % (question, order)
        question_option.save()

        option_content = self.cleaned_data.get("content")
        question_option.content = process_mathml_content(
            option_content,
            Mathml.TESTING_QUESTION_OPTION,
            question_option.id
        )

        question_option.save()

        return question_option

    class Meta:
        model = TestingQuestionOption


class TestingQuestionFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(TestingQuestionFormSet, self).__init__(*args, **kwargs)
        initial = []
        for i in range(1, self.queryset.count() + 4):
            initial.append({'order': i})
        self.initial = initial

    def clean(self):
        super(TestingQuestionFormSet, self).clean()

        question_options = []
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            data = form.cleaned_data
            data["order"] = TestingQuestionOption.objects.filter(question__name=self.data.get("name")).count()
            data["name"] = "%s Option %s" % (self.data.get("name"), data.get("order"))
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

    def get_order(self, question):
        results = TestingQuestionOption.objects.filter(question=question).aggregate(Max("order"))

        if results and "order__max" in results and results["order__max"]:
            max_order = results["order__max"]
            max_order += 1
        else:
            max_order = 1

        return max_order

    def save(self, commit=True):
        options = super(TestingQuestionFormSet, self).save(commit=False)
        if options:
            question = options[0].question
            existing_options = TestingQuestionOption.objects.filter(question=question).count()

            for option in options:
                if option.order == 0:
                    option.order = self.get_order(question)
                if option.name == "Auto Generated":
                    option.name = "%s Option %s" % (question, option.order)
                option.save()

            if (len(options) + existing_options) < 2:
                order = self.get_order(question)
                name = "%s Option %s" % (question, order)
                TestingQuestionOption.objects.create(name=name, order=order, question=question, correct=False)


def process_mathml_content(_content, _source, _source_id):
    _content = convert_to_tags(_content)

    pattern = "<[a-zA-Z0-9]*[:]*math.*?>.*?</[a-zA-Z0-9]*[:]*math>"
    mathml = re.findall(pattern, _content)

    for m in mathml:
        _content = re.sub(pattern, process_mathml_tag(m, _source, _source_id), _content, count=1)

    return _content


def process_mathml_tag(_content, _source, _source_id):
    image_format = 'PNG'

    directory = settings.MEDIA_ROOT

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
    max_size = 300
    image_format = 'PNG'
    quality = 3
    directory = settings.MEDIA_ROOT

    # get all the mathml objects that have not been rendered
    not_rendered = Mathml.objects.filter(rendered=False)

    for nr in not_rendered:
        try:
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
        except Exception as ex:
            logger.warning("Error while cleaning mathml %s of source %s. Reason: %s"
                           % (nr.filename, nr.source_id, ex.message))
            # error while trying to clean-up
            continue

        # get the mathml content
        content = convert_to_tags(nr.mathml_content)
        values = {'mathml': content,
                  'max_size': max_size,
                  'image_format': image_format,
                  'quality': quality}

        try:
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
        except Exception as ex:
            logger.warning("Error while posting/processing request for mathml %s of source %s. Reason: %s"
                           % (nr.filename, nr.source_id, ex.message))


class GoldenEggCreateForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.all())

    def clean_classs(self):
        course = self.data.get("course")
        classs = self.cleaned_data.get("classs")
        active = self.data.get("active") == "on"
        active_golden_eggs_class = GoldenEgg.objects.filter(classs=classs, active=True)
        active_golden_eggs_course = GoldenEgg.objects.filter(course=course, classs=None, active=True)
        if (active_golden_eggs_class.exists() or active_golden_eggs_course.exists()) and active:
            raise forms.ValidationError("There can only be one active Golden Egg per class")
        if active_golden_eggs_course.exists() and active:
            raise forms.ValidationError("There can only be one active Golden Egg per class")
        if active_golden_eggs_class.exists() and active:
            raise forms.ValidationError("There can only be one active Golden Egg per class")
        return classs

    def clean_course(self):
        classs = self.cleaned_data.get("classs")
        course = self.cleaned_data.get("course")
        active = self.data.get("active") == "on"
        classes = Class.objects.filter(course=course)
        if not classs:
            active_golden_eggs = GoldenEgg.objects.filter(classs__in=classes, active=True)
            if active_golden_eggs.exists() and active:
                raise forms.ValidationError("There can only be one active Golden Egg per class")
        active_golden_eggs = GoldenEgg.objects.values_list("classs").filter(classs__in=classes, active=True)
        classes = Class.objects.filter(id__in=active_golden_eggs)
        if active and classs in classes:
            raise forms.ValidationError("There can only be one active Golden Egg per class")
        return course

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


class EventForm(forms.ModelForm):

    def clean(self):
        data = self.cleaned_data
        if data.get('event_points') is None and data.get('airtime') is None and data.get('event_badge') is None:
            msg = u"One award must be awarded."
            self._errors["event_points"] = self.error_class([msg])
            self._errors["airtime"] = self.error_class([msg])
            self._errors["event_badge"] = self.error_class([msg])

        elif data.get('event_points') and (data.get('airtime') or data.get('event_badge')):
            msg = u"Only award can be awarded."
            self._errors["event_points"] = self.error_class([msg])
            self._errors["airtime"] = self.error_class([msg])
            self._errors["event_badge"] = self.error_class([msg])

        if data.get('activation_date'):
            if data.get('activation_date') < datetime.now():
                msg = u"Invalid date selected."
                self._errors["activation_date"] = self.error_class([msg])
        else:
            msg = u"Select a valid date."
            self._errors["activation_date"] = self.error_class([msg])

        if not data.get('deactivation_date'):
            msg = u"Invalid date selected."
            self._errors["deactivation_date"] = self.error_class([msg])
        else:
            if data.get('deactivation_date') < datetime.now() or \
                    data.get('deactivation_date') < data.get('activation_date'):
                msg = u"Select a valid date."
                self._errors["deactivation_date"] = self.error_class([msg])

        return data

    class Meta:
        model = Event


class EventSplashPageInlineFormSet(forms.models.BaseInlineFormSet):

    def clean(self):
        super(EventSplashPageInlineFormSet, self).clean()
        splash_pages = []
        if not hasattr(self.form, 'cleaned_data'):
            for form in self.forms:
                data = form.cleaned_data
                if not data.get('DELETE') and data.get('order_number') is not None and data.get('header') is not None \
                        and data.get('paragraph') is not None:
                    if any(d['order_number'] == data.get('order_number') for d in splash_pages):
                        raise forms.ValidationError({'name': ['Order number cannot be repeated.', ]})
                    else:
                        splash_pages.append(data)

            if len(splash_pages) < 1:
                raise forms.ValidationError({'name': ['You  must create at least one splash page.', ]})

            splash_pages = sorted(splash_pages, key=lambda k: k['order_number'])

            count = 0
            for page in splash_pages:
                count += 1
                if page.get('order_number') != count:
                    raise forms.ValidationError({'name': ["Order number's must be between 1 and %s." %
                                                          len(splash_pages), ]})


class EventStartPageInlineFormSet(forms.models.BaseInlineFormSet):

    def clean(self):
        super(EventStartPageInlineFormSet, self).clean()
        if not hasattr(self.form, 'cleaned_data'):
            count = 0
            for form in self.forms:
                data = form.cleaned_data
                if data.get('header') is not None and data.get('paragraph') is not None and not data.get('DELETE'):
                    count += 1

            if count == 0:
                raise forms.ValidationError({'name': ['You must create one start page']})


class EventEndPageInlineFormSet(forms.models.BaseInlineFormSet):

    def clean(self):
        super(EventEndPageInlineFormSet, self).clean()
        if not hasattr(self.form, 'cleaned_data'):
            count = 0
            for form in self.forms:
                data = form.cleaned_data
                if data.get('header') is not None and data.get('paragraph') is not None and not data.get('DELETE'):
                    count += 1

            if count == 0:
                raise forms.ValidationError({'name': ['You must create one end page']})

    class Meta:
        model = Event


class EventQuestionRelInline(forms.models.BaseInlineFormSet):

    def clean(self):
        super(EventQuestionRelInline, self).clean()
        if not hasattr(self.form, 'cleaned_data'):
            questions = []
            for form in self.forms:
                data = form.cleaned_data
                if data.get('order') is not None and data.get('question') is not None and not data.get('DELETE'):
                    if any(d['order'] == data.get('order') for d in questions):
                        raise forms.ValidationError({'name': ['Order number cannot be repeated.', ]})
                    if any(d['question'] == data.get('question') for d in questions):
                        raise forms.ValidationError({'name': ['Questions cannot be repeated.', ]})
                    questions.append(data)

            if len(questions) < 1:
                raise forms.ValidationError({'name': ['You must add at least one question to the event.']})

            questions = sorted(questions, key=lambda k: k['order'])

            count = 0
            for page in questions:
                count += 1
                if page.get('order') != count:
                    raise forms.ValidationError({'name': ["Order number's must start with 1 and increment by 1 for "
                                                          "each questions added.", ]})


class SUMitEndPageInlineFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(SUMitEndPageInlineFormSet, self).__init__(*args, **kwargs)
        self.initial = [{'type': '1'}, {'type': '2'}, {'type': '3'}]

    def clean(self):
        super(SUMitEndPageInlineFormSet, self).clean()
        if not hasattr(self.form, 'cleaned_data'):
            count = 0
            count_level1_4 = 0
            count_level5 = 0
            count_winner = 0
            for form in self.forms:
                data = form.cleaned_data
                if data.get('header') is not None and data.get('paragraph') is not None and not data.get('DELETE'):
                    count += 1
                if data.get('type') == 1:
                    count_level1_4 += 1
                if data.get('type') == 2:
                    count_level5 += 1
                if data.get('type') == 3:
                    count_winner += 1

            if count == 0:
                raise forms.ValidationError({'name': ['You must create one end page']})

            if count_level1_4 != 1 and count_level5 != 1 and count_winner != 1:
                raise forms.ValidationError({'name': ['You must create one of each']})

    class Meta:
        model = SUMitEndPage


class SUMitLevelForm(forms.ModelForm):
    def clean_order(self):
        order = self.data.get("order")
        if 1 < order < 5:
            raise forms.ValidationError("Order must be between 1 and 5")
        return order


class SUMitForm(forms.ModelForm):

    def clean(self):
        data = self.cleaned_data
        if data.get('event_points') is None and data.get('airtime') is None and data.get('event_badge') is None:
            msg = u"One award must be awarded."
            self._errors["event_points"] = self.error_class([msg])
            self._errors["airtime"] = self.error_class([msg])
            self._errors["event_badge"] = self.error_class([msg])

        if data.get('activation_date'):
            if data.get('activation_date') < datetime.now():
                msg = u"Invalid date selected."
                self._errors["activation_date"] = self.error_class([msg])
        else:
            msg = u"Select a valid date."
            self._errors["activation_date"] = self.error_class([msg])

        if not data.get('deactivation_date'):
            msg = u"Invalid date selected."
            self._errors["deactivation_date"] = self.error_class([msg])
        else:
            if data.get('deactivation_date') < datetime.now() or \
                    data.get('deactivation_date') < data.get('activation_date'):
                msg = u"Select a valid date."
                self._errors["deactivation_date"] = self.error_class([msg])

        return data

    class Meta:
        model = Event