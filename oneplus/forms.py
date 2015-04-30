from django import forms
from django.db import models


class LoginForm(forms.Form):
    username = forms.CharField(label="Phone Number")
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )


class SmsPasswordForm(forms.Form):
    msisdn = forms.CharField(label="Phone Number")


class ChangeDetailsForm(forms.Form):
    old_number = forms.CharField(label="Old Number",
                                 max_length=13)
    new_number = forms.CharField(label="New Number",
                                 max_length=13)
    old_email = forms.CharField(label="Old Email",
                                max_length=13)
    new_email = forms.CharField(label="New Email",
                                max_length=13)