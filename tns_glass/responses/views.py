from django.core.exceptions import ValidationError
from django.template import RequestContext
from wetmills.models import *
from csps.models import *
from django.shortcuts import render_to_response
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from rapidsms_xforms.views import XForm, XFormFieldConstraint
from blurbs.models import Blurb
from sms_reports.models import Report
from cc.models import MessageCC
from .forms import ReportForm
from help.models import HelpMessage

from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from django import forms
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

class ResponseForm(forms.Form):
    response_en = forms.CharField(max_length=255, widget=forms.Textarea)
    response_rw = forms.CharField(max_length=255, widget=forms.Textarea)
    response_tz_sw = forms.CharField(max_length=255, widget=forms.Textarea)
    response_am = forms.CharField(max_length=255, widget=forms.Textarea)
    constraint_id = forms.CharField(widget=forms.HiddenInput, required=False)
    form_id = forms.CharField(widget=forms.HiddenInput, required=False)
    blurb_id = forms.CharField(widget=forms.HiddenInput, required=False)
    cc_id = forms.CharField(widget=forms.HiddenInput, required=False)
    label = forms.CharField(widget=forms.HiddenInput, required=False)

class KeywordForm(forms.Form):
    def __init__(self, xform, *args, **kwargs):
        self.xform = xform
        super(KeywordForm, self).__init__(*args, **kwargs)

    extra_keywords = forms.CharField(max_length=255, required=False,
                                     help_text=_("Any other keywords you want active for this form"))

    def clean_extra_keywords(self):
        extra_keywords = self.cleaned_data['extra_keywords'].lower().split()

        for keyword in extra_keywords:
            if XForm.objects.filter(keyword__contains=" %s ").exclude(pk=self.xform.pk) or XForm.objects.filter(keyword__startswith="%s " % keyword).exclude(pk=self.xform.pk):
                raise ValidationError(_("The keyword '%s' is already taken by another form.") % keyword)

        return " ".join(extra_keywords)


@login_required
def forms(request):
    """
    List of all the forms on the site
    """
    xforms = XForm.on_site.all().exclude(keyword__in=['store', 'send', 'cash', 'sc', 'cherry', 'lookup', 'rec', 'return', 'sum', 'test']).order_by('keyword')

    forms = []
    
    for form in xforms:
        fields = form.fields.all()
        constraints = []

        for field in fields:
            for constraint in field.constraints.all():
                constraints.append(constraint)
                
        forms.append({ 'form': form, 'fields': form.fields.all(), 'constraints' : constraints })

    reports = None
    
    return render_to_response(
        "responses/forms.html", 
        { 'xforms': xforms, 'forms':forms, 'reports':reports, 'helps': HelpMessage.objects.all().order_by('-priority') },
        context_instance=RequestContext(request))

def responses(request, form_id):
    """
    Get all the responses for the given form
    """
    form = XForm.on_site.get(pk=form_id)
    fields = form.fields.all()
    constraints = []
    initial = []
    keyword_form = KeywordForm(form, initial=dict(extra_keywords=" ".join(form.get_extra_keywords())))

    has_errors = False

    # Add the overall form response
    initial.append({'label': _('Response message for successful submission for %s') % form.name,
                    'response_en' : form.response_en_us,
                    'response_rw': form.response_rw,
                    'response_tz_sw': form.response_tz_sw,
                    'response_am': form.response_am,
                    'form_id' : form.id })

    # Add any form blurbs
    blurbs = Blurb.objects.filter(form=form.id)
    for blurb in blurbs:
        initial.append({'label': blurb.description,
                        'response_en': blurb.message_en_us,
                        'response_rw': blurb.message_rw,
                        'response_tz_sw': blurb.message_tz_sw,
                        'response_am': blurb.message_am,
                        'blurb_id':blurb.id})
    
    # Add in constraint messages
    for field in fields:
        for constraint in field.constraints.all():
            constraints.append(constraint)
            label = get_constraint_message(constraint)
            initial.append({'label':label,
                            'response_en': constraint.message_en_us,
                            'response_rw': constraint.message_rw,
                            'response_tz_sw': constraint.message_tz_sw,
                            'response_am': constraint.message_am,
                            'constraint_id': constraint.id })

    # Also add in any cc's
    for cc in MessageCC.objects.filter(form=form):
        initial.append({'label': cc.description,
                        'response_en': cc.message_en_us,
                        'response_rw': cc.message_rw,
                        'response_tz_sw': cc.message_tz_sw,
                        'response_am': cc.message_am,
                        'cc_id': cc.id})

    ResponseFormSet = formset_factory(ResponseForm, extra=0)
    if request.method == 'POST':
        formset = ResponseFormSet(request.POST)

        keyword_form = KeywordForm(form, request.POST)
        if keyword_form.is_valid():
            form.keyword = "%s %s " % (form.get_primary_keyword(), keyword_form.cleaned_data['extra_keywords'])
            form.save()

        try:
            if keyword_form.is_valid() and formset.is_valid():
                for cleaned in formset.cleaned_data:
                    if 'form_id' in cleaned and len(cleaned['form_id']) > 0:
                        form_id = int(cleaned['form_id'])
                        form = XForm.on_site.get(pk=form_id)
                        form.response_en_us = cleaned['response_en']
                        form.response_rw = cleaned['response_rw']
                        form.response_tz_sw = cleaned['response_tz_sw']
                        form.response_am = cleaned['response_am']
                        form.save()
                    elif 'constraint_id' in cleaned and len(cleaned['constraint_id']) > 0:
                        constraint_id = int(cleaned['constraint_id'])
                        constraint = XFormFieldConstraint.objects.get(pk=constraint_id)
                        constraint.message_en_us = cleaned['response_en']
                        constraint.message_rw = cleaned['response_rw']
                        constraint.message_tz_sw = cleaned['response_tz_sw']
                        constraint.message_am = cleaned['response_am']
                        constraint.save()
                    elif 'blurb_id' in cleaned and len(cleaned['blurb_id']) > 0:
                        blurb_id = int(cleaned['blurb_id'])
                        blurb = Blurb.objects.get(pk=blurb_id)
                        blurb.message_en_us = cleaned['response_en']
                        blurb.message_rw = cleaned['response_rw']
                        blurb.message_tz_sw = cleaned['response_tz_sw']
                        blurb.message_am = cleaned['response_am']
                        blurb.save()
                    elif 'cc_id' in cleaned and len(cleaned['cc_id']) > 0:
                        cc_id = int(cleaned['cc_id'])
                        cc = MessageCC.objects.get(pk=cc_id)
                        cc.message_en_us = cleaned['response_en']
                        cc.message_rw = cleaned['response_rw']
                        cc.message_tz_sw = cleaned['response_tz_sw']
                        cc.message_am = cleaned['response_am']
                        cc.save()

                messages.success(request, "Responses saved.")
                return HttpResponseRedirect(reverse('xform-list'))
            else:
                has_errors = True
        except:
            import traceback
            traceback.print_exc()
            messages.error(request, _("An error ocurred saving your responses, please check their format."))
    else:
        formset = ResponseFormSet(initial=initial)


    return render_to_response(
        "responses/edit.html", 
        { 'form': form,
          'keyword_form': keyword_form,
          'fields': form.fields.all(), 
          'constraints' : constraints, 
          'formset': formset, 
          'has_errors': has_errors},
        context_instance=RequestContext(request))

def report_edit(request, report_id):

    report = Report.objects.get(pk=report_id)
    form = ReportForm(initial=dict(message_en_us=report.message_en_us,
                                   message_rw=report.message_rw))

    if request.POST:
        form = ReportForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            report.message_en_us = cleaned['message_en_us']
            report.message_rw = cleaned['message_rw']
            report.save()
            messages.success(request, "Report message saved")
            return HttpResponseRedirect(reverse('xform-list'))
    
    return render_to_response(
        "responses/edit_report.html", 
        { 'report':report, 'form':form },
        context_instance=RequestContext(request))


def get_constraint_message(constraint):

    if constraint.type == "max_len":
        return _("Supplied length for '%s' is not less than %s characters") % (constraint.field, constraint.test)
    elif constraint.type == "min_len":
        return _("Supplied length for '%s' is not greater than %s characters") % (constraint.field, constraint.test)
    elif constraint.type == "min_val":
        return _("Supplied value for '%s' is not %s or greater") % (constraint.field, constraint.test)
    elif constraint.type == "max_val":
        return _("Supplied value for '%s' is not %s or less") % (constraint.field, constraint.test)
    elif constraint.type == "req_val":
        return _("Required field '%s' is missing from submission") % (constraint.field)
    elif constraint.type == "regex":
        return _("Supplied value for '%s' does not match the regex '%s'") % (constraint.field, constraint.test)

    return _("Error message for '%s'") % constraint.field.name
