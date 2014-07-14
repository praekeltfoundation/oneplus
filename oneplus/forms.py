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
