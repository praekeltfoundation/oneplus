from django import forms
from organisation.models import School
from core.models import Class


class LoginForm(forms.Form):
    username = forms.CharField(label="Phone Number")
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )


class SmsPasswordForm(forms.Form):
    msisdn = forms.CharField(label="Phone Number")


class SignupForm(forms.Form):
    ENROLLED_CHOICES = (
        ("0", "Yes"),
        ("1", "No")
    )

    GRADE_CHOICES = (
        ('Grade 10', 'Grade 10'),
        ('Grade 11', 'Grade 11'),
        ('Grade 12', 'Grade 12')
    )

    first_name = forms.CharField(label="First Name",
                                 max_length=30,
                                 required=True)
    surname = forms.CharField(label="Surname",
                              max_length=30,
                              required=True)
    cellphone = forms.CharField(label="Cellphone Number(e.g. 0724391733)",
                                max_length=50,
                                required=True)
    school = forms.ModelChoiceField(queryset=School.objects.all(),
                                    label="School",
                                    required=True)
    classs = forms.ModelChoiceField(queryset=Class.objects.all(),
                                    label="Class",
                                    required=True)
    area = forms.CharField(label="Area(Suburb)",
                           max_length=50,
                           required=True)
    city = forms.CharField(label="City",
                           max_length=50,
                           required=True)
    country = forms.CharField(label="Country",
                              max_length=50,
                              required=True)
    enrolled = forms.ChoiceField(label="Are you currently enrolled in a ProMaths class?",
                                 widget=forms.RadioSelect,
                                 choices=ENROLLED_CHOICES,
                                 required=True)
    grade = forms.ChoiceField(label="What is your current grade?",
                              widget=forms.RadioSelect,
                              choices=GRADE_CHOICES,
                              required=True, )

