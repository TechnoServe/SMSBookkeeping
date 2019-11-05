from smartmin.users.views import UserCRUDL as SmartUserCRUDL, UserProfileForm
from smartmin.views import *
from wetmills.models import Wetmill
from locales.models import Country
from csps.models import CSP
from guardian.shortcuts import remove_perm
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
import re

class UserCRUDL(SmartUserCRUDL):
    actions = ('create', 'list', 'update', 'profile', 'forget', 'recover', 'expired', 'failed', 'newpassword', 'permissions', 'mimic')

    def permission_for_action(self, action):
        """
        Returns the permission to use for the passed in action
        """
        return "%s.%s_%s" % ('auth', self.model_name.lower(), action)

    def template_for_action(self, action):
        """
        Returns the template to use for the passed in action
        """
        return "%s/%s_%s.html" % ('users', self.model_name.lower(), action)

    def url_name_for_action(self, action):
        """
        Returns the reverse name for this action
        """
        return "%s.%s_%s" % ('users', self.model_name.lower(), action)

    class Create(SmartUserCRUDL.Create):
        success_url = "id@users.user_permissions"
        fields = ('username', 'new_password', 'site_administrator', 'country_administrator', 'sms_administrator',
                  'compliance_officer', 'web_accountant', 'private_wet_mill_owner', 'financial_institution_member', 'first_name', 'last_name', 'email')

        def get_form(self, form_class):
            form = super(UserCRUDL.Create, self).get_form(form_class)
            form.fields.insert(len(form.fields), "site_administrator", 
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user a site administrator who has all privileges")))
            form.fields.insert(len(form.fields), "country_administrator", 
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user a country administrator")))
            form.fields.insert(len(form.fields), "sms_administrator",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user an SMS administrator")))
            form.fields.insert(len(form.fields), "compliance_officer",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user a compliance officer that doesn't get to see financial data (guatemala)")))
            form.fields.insert(len(form.fields), "web_accountant",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user an accountant that enters data through the website (guatemala)")))
            form.fields.insert(len(form.fields), "private_wet_mill_owner",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user a private wet mill owner")))
            form.fields.insert(len(form.fields), "financial_institution_member",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this a financial institution member")))
            return form

        def save_m2m(self):
            super(UserCRUDL.Create, self).save_m2m()

            administrator_group = Group.objects.get(name="Administrators")
            self.object.groups.remove(administrator_group)
            if self.form.cleaned_data['site_administrator']:
                self.object.groups.add(administrator_group)

            group = Group.objects.get(name="Country Administrators")
            self.object.groups.remove(group)
            if self.form.cleaned_data['country_administrator']:
                self.object.groups.add(group)

            group = Group.objects.get(name="SMS Administrators")
            self.object.groups.remove(group)
            if self.form.cleaned_data['sms_administrator']:
                self.object.groups.add(group)

            group = Group.objects.get(name="Compliance Officers")
            self.object.groups.remove(group)
            if self.form.cleaned_data['compliance_officer']:
                self.object.groups.add(group)

            group = Group.objects.get(name="Web Accountant")
            self.object.groups.remove(group)
            if self.form.cleaned_data['web_accountant']:
                self.object.groups.add(group)

            group = Group.objects.get(name="Private Wet Mill Owners")
            self.object.groups.remove(group)
            if self.form.cleaned_data['private_wet_mill_owner']:
                self.object.groups.add(group)

            group = Group.objects.get(name="Financial Institution Member")
            self.object.groups.remove(group)
            if self.form.cleaned_data['financial_institution_member']:
                self.object.groups.add(group)

    class Update(SmartUserCRUDL.Update):
        template_name = 'users/user_update.html'
        fields = ('is_active', 'username', 'new_password', 'site_administrator', 'country_administrator',
                  'sms_administrator', 'compliance_officer', 'web_accountant', 'private_wet_mill_owner', 'financial_institution_member', 'first_name', 'last_name', 'email')

        def get_form(self, form_class):
            form = super(UserCRUDL.Update, self).get_form(form_class)
            form.fields.insert(len(form.fields), "site_administrator", 
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user a site administrator who has all privileges")))
            form.fields.insert(len(form.fields), "country_administrator", 
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user a country administrator")))
            form.fields.insert(len(form.fields), "sms_administrator",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user an SMS administrator")))
            form.fields.insert(len(form.fields), "compliance_officer",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user a compliance officer that doesn't get to see financial data (guatemala)")))
            form.fields.insert(len(form.fields), "web_accountant",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user an accountant that enters data through the website (guatemala)")))
            form.fields.insert(len(form.fields), "private_wet_mill_owner",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this user a private wet mill owner")))
            form.fields.insert(len(form.fields), "financial_institution_member",
                               forms.BooleanField(required=False,
                                                  help_text=_("Is this a financial institution member")))
            return form

        def save_m2m(self):
            super(UserCRUDL.Update, self).save_m2m()

            group = Group.objects.get(name="Administrators")
            self.object.groups.remove(group)
            if self.form.cleaned_data['site_administrator']:
                self.object.groups.add(group)

            group = Group.objects.get(name="Country Administrators")
            self.object.groups.remove(group)
            if self.form.cleaned_data['country_administrator']:
                self.object.groups.add(group)

            group = Group.objects.get(name="SMS Administrators")
            self.object.groups.remove(group)
            if self.form.cleaned_data['sms_administrator']:
                self.object.groups.add(group)

            group = Group.objects.get(name="Compliance Officers")
            self.object.groups.remove(group)
            if self.form.cleaned_data['compliance_officer']:
                self.object.groups.add(group)

            group = Group.objects.get(name="Private Wet Mill Owners")
            self.object.groups.remove(group)
            if self.form.cleaned_data['private_wet_mill_owner']:
                self.object.groups.add(group)

            group = Group.objects.get(name="Financial Institution Member")
            self.object.groups.remove(group)
            if self.form.cleaned_data['financial_institution_member']:
                self.object.groups.add(group)


        def derive_initial(self, *args, **kwargs):
            initial = super(UserCRUDL.Update, self).derive_initial(*args, **kwargs)
            if self.object.groups.filter(name="Administrators"):
                initial['site_administrator'] = True

            if self.object.groups.filter(name="Country Administrators"):
                initial['country_administrator'] = True

            if self.object.groups.filter(name="SMS Administrators"):
                initial['sms_administrator'] = True

            if self.object.groups.filter(name="Compliance Officers"):
                initial['compliance_officer'] = True

            if self.object.groups.filter(name="Web Accountant"):
                initial['web_accountant'] = True

            if self.object.groups.filter(name="Private Wet Mill Owners"):
                initial['private_wet_mill_owner'] = True

            if self.object.groups.filter(name="Financial Institution Member"):
                initial['financial_institution_member'] = True

            return initial

    class Permissions(SmartUpdateView):
        template_name = 'users/user_permissions.html'
        title = "Edit User Permissions"
        success_url = "@users.user_list"
        success_message = "Your user permissions have been saved."

        PERMS = ('wetmill_edit', 'report_view', 'report_edit', 'scorecard_view', 'scorecard_edit', 'sms_view', 'sms_edit')
        APP_OBJECTS = ('locales.country', 'csps.csp', 'wetmills.wetmill')

        def add_check_fields(self, form, objects, name, field_dict):
            for obj in objects:
                fields = []
                for perm in self.PERMS:
                    check_field = forms.BooleanField(required=False)
                    field_name = '%s__%s_%d' % (perm, name, obj.id)

                    form.fields.insert(len(form.fields), field_name, check_field)
                    fields.append(field_name)

                # stuff it in our dict
                field_dict[obj] = fields

        def derive_initial(self):
            # load all our wetmills, ordered by country then order
            self.countries = Country.objects.filter(is_active=True).order_by('name')
            self.wetmills = Wetmill.objects.filter(is_active=True).order_by('country__name', 'name').select_related('country')
            self.csps = CSP.objects.filter(is_active=True).order_by('country__name', 'name')

            initial = dict()
            for app_object in self.APP_OBJECTS:
                (app_name, obj_name) = app_object.split('.')
                for perm in self.PERMS:
                    permission = '%s_%s' % (app_object, perm)
                    for obj in get_objects_for_user(self.object, permission):
                        key = "%s__%s_%d" % (perm, obj_name, obj.id)
                        initial[key] = True

            return initial

        def get_form(self, form_class):
            form = super(UserCRUDL.Permissions, self).get_form(form_class)
            form.fields.clear()

            self.country_fields = dict()
            self.csp_fields = dict()
            self.wetmill_fields = dict()

            self.add_check_fields(form, self.countries, 'country', self.country_fields)
            self.add_check_fields(form, self.csps, 'csp', self.csp_fields)
            self.add_check_fields(form, self.wetmills, 'wetmill', self.wetmill_fields)

            return form

        def load_object(self, obj_type, obj_id):
            if obj_type == 'country':
                return Country.objects.get(pk=obj_id)
            elif obj_type == 'csp':
                return CSP.objects.get(pk=obj_id)
            elif obj_type == 'wetmill':
                return Wetmill.objects.get(pk=obj_id)

        def save_m2m(self):
            """
            We actually do the job of assigning permissions here
            """
            # first we remove all the permissions this user has been granted
            for obj_type in ('locales.country', 'csps.csp', 'wetmills.wetmill'):
                for perm in self.PERMS:
                    permission = '%s_%s' % (obj_type, perm)
                    for obj in get_objects_for_user(self.object, permission):
                        remove_perm(permission, self.object, obj)

            for field in self.form.fields:
                if self.form.cleaned_data[field]:
                    matcher = re.match("(\w+)__(\w+)_(\d+)", field)
                    if matcher:
                        obj_type = matcher.group(2)
                        permission = matcher.group(1)
                        obj = self.load_object(matcher.group(2), matcher.group(3))
                        assign("%s_%s" % (obj_type, permission), self.object, obj)

        def get_context_data(self, **kwargs):
            context = super(UserCRUDL.Permissions, self).get_context_data(**kwargs)

            context['countries'] = self.countries
            context['csps'] = self.csps
            context['wetmills'] = self.wetmills

            context['country_fields'] = self.country_fields
            context['csp_fields'] = self.csp_fields
            context['wetmill_fields'] = self.wetmill_fields

            return context
