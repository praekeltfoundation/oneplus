from django import forms
from .models import TestingQuestion


class AddTestingQuestionForm(forms.ModelForm):
    module = forms.CharField(error_messages={'required': 'A Test question needs to be associated with a module.'})

    class Meta:
        model = TestingQuestion