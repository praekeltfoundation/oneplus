from django import forms
from content.models import TestingQuestion, TestingQuestionOption, Module, Mathml
import re
import uuid
import os


class TestingQuestionCreateForm(forms.ModelForm):
    module = forms.ModelChoiceField(queryset=Module.objects.all(),
                                    error_messages={'required': 'A Test question needs to '
                                                                'be associated with a module.'})

    def save(self, commit=True):
        testing_question = super(TestingQuestionCreateForm, self).save(commit=False)
        question_content = self.cleaned_data.get("question_content")

        m = re.findall("<math.*?>.*?</math>", question_content)
        for a in m:
            question_content = re.sub("<math.*?>.*?</math>",
                                      process_mathml_content(a, 0, self.id),
                                      question_content, count=1)

        testing_question.question_content = question_content

        answer_content = self.cleaned_data.get("answer_content")

        m = re.findall("<math.*?>.*?</math>", answer_content)
        for a in m:
            answer_content = re.sub("<math.*?>.*?</math>",
                                    process_mathml_content(a, 1, self.id),
                                    answer_content, count=1)

        testing_question.answer_content = answer_content

        if commit:
            testing_question.save()

        return testing_question

    class Meta:
        model = TestingQuestion


class TestingQuestionOptionCreateForm(forms.ModelForm):
    def save(self, commit=True):
        question_option = super(TestingQuestionOptionCreateForm, self).save(commit=False)
        option_content = self.cleaned_data.get("content")

        m = re.findall("<math.*?>.*?</math>", option_content)
        for a in m:
            option_content = re.sub("<math.*?>.*?</math>",
                                    process_mathml_content(a, 2, self.id),
                                    option_content, count=1)

        question_option.content = option_content

        if commit:
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
    unique_filename = str(uuid.uuid4()) + '.png'

    while True:
        if not os.path.isfile(unique_filename):
            break
        else:
            unique_filename = str(uuid.uuid4()) + ".png"

    Mathml.objects.create(mathml_content=_content,
                          filename=unique_filename,
                          source=_source,
                          source_id=_source_id)

    return "<img src='%s' />" % unique_filename