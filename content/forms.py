from django import forms
from .models import TestingQuestion


class TestingQuestionCreateForm(forms.ModelForm):
    module = forms.CharField(error_messages={'required': 'A Test question needs to be associated with a module.'})

    class Meta:
        model = TestingQuestion


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
            raise forms.ValidationError("A minimum of 2 questions must be added.")

        correct_selected = False
        for qo in question_options:
            if qo is True:
                correct_selected = True
                break

        if correct_selected is False:
            raise forms.ValidationError("One correct answer is required.")