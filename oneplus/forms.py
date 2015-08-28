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


class ResetPassword(forms.Form):
    password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput
    )

    password_2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput
    )