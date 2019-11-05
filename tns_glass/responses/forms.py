from django import forms
from django.forms import ModelForm
from reports.models import Report


class ReportForm(forms.Form):
    message_en_us = forms.CharField(max_length=200, required=False, help_text="", label="Message (en)")
    message_rw = forms.CharField(max_length=200, required=False, help_text="", label="Message (rw)")
    message_tz_sw = forms.CharField(max_length=200, required=False, help_text="", label="Message (tz)")
