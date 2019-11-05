from django.contrib.auth.models import User
from django.db.models.signals import pre_save
import pytz
import re
from datetime import datetime, timedelta, date
from decimal import Decimal

from django.db import models
from django.db.models import Avg, Sum
from django.forms import ValidationError
from django.conf import settings

from rapidsms_xforms.models import XForm, XFormField, xform_received, XFormSubmission
from rapidsms.models import Connection, Backend
from rapidsms.messages.incoming import IncomingMessage

from locales.models import Country
from wetmills.models import Wetmill
from csps.models import CSP
from seasons.models import Season
from cc.models import MessageCC
from blurbs.models import Blurb, render
from django.utils.translation import activate
from locales.models import comma_formatted
from django.utils.translation import ugettext_lazy as _

from tasks import approve_submission

# this is needed for South, EAV defines some new fields, we need to reassure South they work as normal
# see: http://south.aeracode.org/wiki/MyFieldsDontWork
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^eav\.fields\.EavSlugField"])
add_introspection_rules([], ["^eav\.fields\.EavDatatypeField"])

# an hour is 60 second * 60 minutes
ONE_HOUR = 60 * 60

def get_country_for_backend(backend):
    country_code = settings.BACKEND_TO_COUNTRY_MAP.get(backend.lower(), 'RW')
    return Country.objects.get(country_code__iexact=country_code)

def get_season(country):
    season = Season.objects.filter(country=country, is_active=True).order_by('-name')
    return season[0]

def from_country_weight(weight, country): 
    return Decimal(str(weight)) / country.weight.ratio_to_kilogram

def to_country_weight(weight, country):
    local_weight = 0
    if weight:
        local_weight = Decimal(weight) / Decimal(country.weight.ratio_to_kilogram)

    return Decimal(local_weight).quantize(Decimal(".01"))

def send_wetmill_ccs(sender, form, wetmill, variables):
    """
    Sends all the CCs for this form using the passed in variables.  This only works
    for those messages that are wetmill centric.
    """
    # look up any cc messages for this form
    ccs = MessageCC.objects.filter(form=form)
    if not ccs:
        return

    # for each of our CC's, build a recipient list and send it off
    for cc in ccs:
        # our recipients
        recipients = []

        # look up our message based on our types
        for reporter_type in cc.reporter_types.all():
            model = reporter_type.model_class()
            matches = model.objects.filter(wetmill=wetmill)
            for match in matches:
                recipients.append(match)

        # send our CC off
        if recipients:
            cc.send(sender, recipients, variables)

def check_wetmill_type(submission, wetmill, types):
    """
    Tests the wetmill system type vs the passed in type, returning if there is an error.
    """
    if wetmill.get_accounting_system() not in types:
        submission.has_errors = True
        submission.save()
        submission.response = Blurb.get(submission.xform, "unsupported", submission.template_vars,
                                        "The {{ wetmill.name }} wet mill does not support this message.")
        return True
    else:
        return False

class ActiveManager(models.Manager):
    """
    A manager that only selects items which are still active.
    """
    def get_query_set(self):
        """
        Where the magic happens, we automatically throw on an extra active = True to every filter
        """
        return super(ActiveManager, self).get_query_set().filter(active=True)

class Actor(models.Model):
    """
    Represents someone who interacts with our system.  Common fields are the name, connection,
    creation date, and language
    """
    connection = models.ForeignKey(Connection, verbose_name=_("Connection"))
    name = models.CharField(max_length=128, verbose_name=_("Name"))
    language = models.CharField(max_length=5, default="rw", verbose_name=_("Language"))
    active = models.BooleanField(default=True, verbose_name=_("Active"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created"))

    objects = ActiveManager()
    all = models.Manager()

    def phone(self): # pragma: no cover
        if self.connection:
            return self.connection.identity[-10:]
        else:
            return ""

    class Meta:
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s" % (self.name)

class WetmillObserver(Actor):
    """
    Someone who is observing a wetmill.
    """
    wetmill = models.ForeignKey(Wetmill, null=True, blank=True, verbose_name=_("Wetmill"))

    objects = ActiveManager()
    all = models.Manager()

    @staticmethod
    def register_observer(sender, **kwargs):
        """
        Our XForms Signal hook for registering observers.
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)

        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'obs' and not submission.has_errors:
            # is there already an observer for this connection and wetmill?
            existing = WetmillObserver.objects.filter(wetmill=submission.eav.obs_wetmill, connection=submission.connection)

            name = submission.eav.obs_name.capitalize()
            if submission.eav.obs_last_name:
                name = "%s %s" % (submission.eav.obs_name.capitalize(), submission.eav.obs_last_name.capitalize())
                
            # one already exists, just update the name
            obs = None
            if existing:  # pragma: no cover
                obs = existing[0]
                obs.name = name
                obs.save()

            # otherwise, create a new one
            else:
                # how many observers already exist for this wetmill?
                count = WetmillObserver.objects.filter(wetmill=submission.eav.obs_wetmill).count()
                if count >= 5:
                    submission.has_errors = True
                    submission.response = Blurb.get(xform, 'too_many', dict(wetmill=submission.eav.obs_wetmill),
                                                    "There are too many registered observers for the {{ wetmill.name }} wet mill.")
                    submission.save()
                else:
                    obs = WetmillObserver.objects.create(connection=submission.connection,
                                                         wetmill=submission.eav.obs_wetmill,
                                                         name=name,
                                                         language=country.language)

                    # send off any cc's
                    send_wetmill_ccs(submission.connection, xform, submission.eav.obs_wetmill, submission.template_vars)

# register as a listener for incoming forms
xform_received.connect(WetmillObserver.register_observer, dispatch_uid='register_observer')

class Accountant(Actor):
    """
    An accountant is associated with a wetmill and is tied to a particular connection.
    """
    wetmill = models.ForeignKey(Wetmill, null=True, blank=True, related_name="accountants", verbose_name=_("Wetmill"))

    objects = ActiveManager()
    all = models.Manager()

    @classmethod
    def for_wetmill(cls, wetmill):
        """
        Returns the registered accountant for a wetmill, or None if there is no accountant
        for that wetmill
        """
        accs = Accountant.objects.filter(wetmill=wetmill).order_by('-created')
        if accs:
            return accs[0]
        else:
            return None

    @staticmethod
    def parse_accountant(command, value, raw=None, connection=None):
        """
        Tries to look up an accountant by phone number, which is the value given
        """
        matches = Accountant.objects.filter(connection__identity=value)
        if matches:
            return matches[0]
        else:  # pragma: no cover
            raise ValidationError("Unable to find accountant with the phone number '%s'"% value)

    @staticmethod
    def pull_accountant(command, message):
        """
        Given a message, figures out what the associated accountant is for this phone number.
        If none is found, then returns None.
        """
        phone = message.connection.identity
        matches = Accountant.objects.filter(connection__identity=phone)
        if matches:
            return phone
        else:
            return None

    @staticmethod
    def register_accountant(sender, **kwargs):
        """
        Our XForms Signal hook for registering accountants.
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)

        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'acc' and not submission.has_errors:
            # is there already an accountant registered for this wetmill?
            existing = Accountant.objects.filter(wetmill=submission.eav.acc_wetmill)

            name = submission.eav.acc_name.capitalize()
            if submission.eav.acc_last_name:
                name = "%s %s" % (submission.eav.acc_name.capitalize(), submission.eav.acc_last_name.capitalize())

            # one already exists 
            if existing:
                existing = existing[0]
                
                # but it is someone different, that's an error
                if existing.connection != submission.connection:
                    submission.has_errors = True
                    submission.response = Blurb.get(xform, 'dupe', dict(existing=existing),
                                                    "An accountant '{{existing.name}}' already exists for this wetmill")

                    submission.save()

                # not someone different, just update
                else:
                    existing.name = name
                    existing.save()
            else:
                # then create a new accountant registrations
                acc = Accountant.objects.create(connection=submission.connection,
                                                wetmill=submission.eav.acc_wetmill,
                                                name=name,
                                                language=country.language)
                
                # send off any cc's
                send_wetmill_ccs(submission.connection, xform, submission.eav.acc_wetmill, submission.template_vars)

# register accountants as valid fields
XFormField.register_field_type('acc', "Accountant", Accountant.parse_accountant,
                               xforms_type='string', db_type=XFormField.TYPE_OBJECT,
                               puller=Accountant.pull_accountant)

# register as a listener for incoming forms
xform_received.connect(Accountant.register_accountant, dispatch_uid='register_accountant')

class CSPOfficer(Actor):
    """
    A CSP officer is associated with a CSP.
    """
    csp = models.ForeignKey(CSP, null=True, blank=True, verbose_name=_("CSP"))

    objects = ActiveManager()
    all = models.Manager()

    def save(self, *args, **kwargs):
        """
        The default language for CSP officers should be en-us, no rw
        """
        if not self.id: self.language = "en-us"
        super(CSPOfficer, self).save(*args, **kwargs)

    @classmethod
    def for_wetmill(cls, wetmill):  # pragma: no cover
        """
        Returns the registered csp for a wetmill, or None if there is no csp officer
        for that wetmill
        """
        officers = CSPOfficer.objects.filter(csp=wetmill.get_csp()).order_by('-created')
        if officers:
            return officers[0]
        else:
            return None

    @staticmethod
    def parse_officer(command, value, raw=None, connection=None):  # pragma: no cover
        """
        Tries to look up an officer by phone number, which is the value given
        """
        matches = CSPOfficer.objects.filter(connection__identity=value)
        if matches:
            return matches[0]
        else:
            raise ValidationError("Unable to find CSP officer with the phone number '%s'"% value)

    @staticmethod
    def pull_officer(command, message):  # pragma: no cover
        """
        Given a message, figures out what the associated officer is for this phone number.
        If none is found, then returns None.
        """
        phone = message.connection.identity
        matches = CSPOfficer.objects.filter(connection__identity=phone)
        if matches:
            return phone
        else:
            return None

    @staticmethod
    def register_officer(sender, **kwargs):  # pragma: no cover
        """
        Our XForms Signal hook for registering CSP officers.
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)

        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'csp' and not submission.has_errors:
            existing = CSPOfficer.objects.filter(connection=submission.connection).exclude(csp=None)

            name = submission.eav.csp_name
            if submission.eav.csp_last_name:  # pragma: no cover
                name = "%s %s" % (submission.eav.csp_name, submission.eav.csp_last_name)

            # a csp officer already exists for this number
            if existing:
                officer = existing[0]

                # this officer belongs to a different csp than what we are registering, that's an error
                if officer.csp and officer.csp != submission.eav.csp_csp:
                    submission.has_errors = True
                    submission.template_vars['existing'] = officer.csp
                    submission.response = Blurb.get(xform, 'already_registered', submission.template_vars,
                                                    "You are already registered with {{ existing.name }}, send 'leave' first to unregister and try again.")
                    return

                # otherwise, this is either the same CSP or we aren't assigned to one, so update
                # our fields
                officer.csp = submission.eav.csp_csp
                officer.name = name
                officer.save()

            # haven't seen this connection before register
            else:
                officer = CSPOfficer.objects.create(connection=submission.connection,
                                                    csp=submission.eav.csp_csp,
                                                    name=name,
                                                    language=country.language)

# register accountants as valid fields
XFormField.register_field_type('csp_off', "CSP Officer", CSPOfficer.parse_officer,
                               xforms_type='string', db_type=XFormField.TYPE_OBJECT,
                               puller=CSPOfficer.pull_officer)

# register as a listener for incoming forms
xform_received.connect(CSPOfficer.register_officer, dispatch_uid='register_officer')

class CPO(Actor):
    """
    A cherry point collection officer, they register with wetmills.
    """
    cpo_id = models.IntegerField(verbose_name=_("CPO ID"))
    wetmill = models.ForeignKey(Wetmill, null=True, blank=True, verbose_name=_("Wetmill"))

    objects = ActiveManager()
    all = models.Manager()

    @staticmethod
    def parse_cpo(command, value, raw=None, connection=None):
        """
        Tries to look up a cpo by the value passed in, which will be the submission id.
        """
        matches = CPO.objects.filter(cpo_id=value)
        if matches:
            return matches[0]
        else:  # pragma: no cover
            raise ValidationError("Unable to find CPO with the id '%s'" % value)

    @staticmethod
    def register_cpo(sender, **kwargs):
        """
        Our XForms Signal hook for registering cpos..
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'sc' and not submission.has_errors:
            # make sure this is supported for this wetmill
            if check_wetmill_type(submission, submission.eav.sc_wetmill, ['FULL']):  # pragma: no cover
                return
            
            # does a cpo already exist for this connection?
            existing = CPO.objects.filter(connection=submission.connection).exclude(wetmill=None)

            name = submission.eav.sc_name
            if submission.eav.sc_last_name:  # pragma: no cover
                name = "%s %s" % (submission.eav.sc_name, submission.eav.sc_last_name)

            cpo = CPO.objects.create(connection=submission.connection,
                                     wetmill=submission.eav.sc_wetmill,
                                     name=name,
                                     cpo_id=submission.confirmation_id,
                                     language=country.language)

            # send off any cc's
            send_wetmill_ccs(submission.connection, xform, submission.eav.sc_wetmill, submission.template_vars)

# register accountants as valid fields
XFormField.register_field_type('cpo', "Site Collector", CPO.parse_cpo,
                               xforms_type='integer', db_type=XFormField.TYPE_OBJECT)

# register as a listener for incoming forms
xform_received.connect(CPO.register_cpo, dispatch_uid='register_cpo')

def add_cpo(wetmill, phone, name):  # pragma: no cover
    """
    Adds a new CPO to the passed in wetmill.  Note this does trigger a CC to be sent
    to the accountant as well as the CPO themselves.
    """
    # first things first, let's create our connection
    (conn, created) = Connection.objects.get_or_create(backend=Backend.objects.get(name="tns"),
                                                       identity="25%s" % phone)

    xform = XForm.objects.get(keyword__startswith='sc')

    # simulate a message coming from their phone
    msg = IncomingMessage(conn, "sc %s %s" % (wetmill.sms_name, name))
    xform.process_sms_submission(msg)


class Farmer(Actor):
    """
    A farmer is associated with a wetmill and is tied to a particular connection.
    """
    wetmill = models.ForeignKey(Wetmill, null=True, blank=True, related_name="farmers", verbose_name=_("Wetmill"))

    objects = ActiveManager()
    all = models.Manager()

    @staticmethod
    def register_farmer(sender, **kwargs):
        """
        Our XForms Signal hook for registering farmers.
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)

        # if this is the farmer form and it does not have errors
        if xform.get_primary_keyword() == 'farmer' and not submission.has_errors:
            # does this connection already exist?
            existing = Farmer.objects.filter(connection=submission.connection, active=True)
            already_registered = False
            moved = False

            for existing_farmer in existing:
                if existing_farmer.wetmill != submission.eav.farmer_wetmill:
                    existing_farmer.active = False
                    existing_farmer.save()
                    moved = True

                else:  
                    already_registered = True

            if not already_registered:
                name = submission.eav.farmer_name.capitalize()
                if submission.eav.acc_last_name:
                    name = "%s %s" % (submission.eav.acc_name.capitalize(), submission.eav.acc_last_name.capitalize())


                farmer = Farmer.objects.create(connection=submission.connection,
                                               wetmill=submission.eav.farmer_wetmill,
                                               name=name,
                                               language=country.language)

            
            # send back our response
            if moved:
                submission.response = Blurb.get(xform, 'farmer_moved', submission.template_vars,
                                                "You are now registered with the {{ wetmill.name }} wetmill, send 'leave' first to unregister")

            elif already_registered: 
                submission.response = Blurb.get(xform, 'farmer_already_registered', submission.template_vars,
                                                "You are already registered with the {{ wetmill.name }} wetmill, send 'leave' first to unregister")


# register as a listener for incoming forms
xform_received.connect(Farmer.register_farmer, dispatch_uid='register_farmer')

# hook in wetmills as valid field types
def parse_wetmill(command, value, raw=None, connection=None):
    """
    Tries to parse a wetmill as a name
    """
    country = get_country_for_backend(connection.backend.name)

    # try to look up this location by name
    wetmills = Wetmill.objects.filter(country=country, sms_name__iexact=value.lower())
    if not wetmills: # pragma: no cover
        raise ValidationError("Unable to find a wet mill with the name '%s'" % value)
    else:
        return wetmills[0]

# register locations as an xform type
XFormField.register_field_type('wetmill', 'Wet Mill', parse_wetmill,
                               xforms_type='string', db_type=XFormField.TYPE_OBJECT)

# hook in CSP's as valid field types
def parse_csp(command, value, raw=None, connection=None):
    """
    Tries to look up a csp by sms_name
    """
    country = get_country_for_backend(connection.backend.name)

    # try to look up this location by name
    csps = CSP.objects.filter(country=country, sms_name__iexact=value.lower())
    if not csps: # pragma: no cover
        raise ValidationError("Unable to find a csp with the name '%s'" % value)
    else:
        return csps[0]

# register locations as an xform type
XFormField.register_field_type('csp', 'CSP', parse_csp,
                               xforms_type='string', db_type=XFormField.TYPE_OBJECT)

def leave(sender, **kwargs):
    """
    Allows users to leave their role.
    """
    xform = kwargs['xform']
    submission = kwargs['submission']

    if xform.get_primary_keyword() == 'leave' and not submission.has_errors:
        # try to find any active actors for this connection
        actors = Actor.objects.filter(connection=submission.connection)

        if actors:
            # send the appropriate CCs

            # accountant?
            acc = Accountant.objects.filter(connection=submission.connection)
            if acc:
                acc = acc[0]
                MessageCC.send_cc(xform, 'acc_leave', submission.connection, WetmillObserver.objects.filter(wetmill=acc.wetmill), dict(user=acc))

            # cpo?
            cpo = CPO.objects.filter(connection=submission.connection)
            if cpo:
                # only one site collector registered for this site
                if len(cpo) == 1:
                    # CC the accountant
                    cpo = cpo[0]
                    MessageCC.send_cc(xform, 'sc_leave', submission.connection, Accountant.objects.filter(wetmill=cpo.wetmill), dict(user=cpo))
                else:
                    # multiple site collectors for this phone, they specified a site collector id though
                    if submission.eav.leave_scid: # pragma: no cover
                        cpo = cpo.filter(cpo_id=submission.eav.leave_scid)

                        # if we found one, CC the accountant
                        if cpo:
                            MessageCC.send_cc(xform, 'sc_leave', submission.connection,
                                              Accountant.objects.filter(wetmill=cpo[0].wetmill), dict(user=cpo))

                            # unregister that actor
                            cpo[0].active = False
                            cpo[0].save()
                            return
                            
                        # otherwise, tell them we couldn't find them
                        else:
                            submission.response = Blurb.get(xform, 'not_found', dict(scid=submission.eav.leave_scid),
                                                            "Unable to find an SC for this wetmill with id: {{ scid }}");
                            submission.has_errors = True
                            submission.save()
                            return

                    # otherwise, tell them there are duplicates for this phone
                    else: # pragma: no cover
                        submission.response = Blurb.get(xform, 'multiple', dict(),
                                                        "Your mobile phone is registered as more than one site collector.  Send 'leave [cpo id]'");
                        submission.has_errors = True
                        submission.save()
                        return

            # observer?
            obs = WetmillObserver.objects.filter(connection=submission.connection)
            if obs:
                obs = obs[0]
                MessageCC.send_cc(xform, 'obs_leave', submission.connection, Accountant.objects.filter(wetmill=obs.wetmill), dict(user=obs))

            # csp
            csp = CSPOfficer.objects.filter(connection=submission.connection)
            if csp:
                csp = csp[0]

            # deactivate them all
            for actor in actors:
                actor.active = False
                actor.save()
        else: # pragma: no cover
            # we couldn't find what this user was all about
            submission.has_errors = True
            submission.reponse = Blurb.get(xform, 'unknown', dict(),
                                           "Your mobile number is not registered with the system.")
            submission.save()

# register a listener for our 'leave' form
xform_received.connect(leave, dispatch_uid='leave')

def lang(sender, **kwargs):
    """
    Allows users to set or query for their language
    """
    xform = kwargs['xform']
    submission = kwargs['submission']

    if xform.get_primary_keyword() == 'lang' and not submission.has_errors:
        # find any contacts for this connection
        contacts = Actor.objects.filter(connection=submission.connection)

        # set the language if they passed it in
        if getattr(submission.eav, 'lang_lang', None):
            lang = submission.eav.lang_lang
            if lang == 'en': lang = 'en-us'

            for contact in contacts:
                contact.language = lang
                contact.save()

        # get our raw language name
        if contacts:
            # active the appropriate language for this user
            activate(contacts[0].language)
            
            lang = 'Kinyarwanda'
            if contacts[0].language == 'en-us':
                lang = 'English'
            elif contacts[0].language == 'tz_sw':
                lang = 'Kiswahili'
            elif contacts[0].language == 'am':
                lang = 'Amharic'

            submission.response = render(xform.response, dict(lang=lang))
        else: # pragma: no cover
            submission.response = Blurb.get(xform, 'unknown', dict(),
                                            "Your mobile number is not registered with the system.")                                            
            submission.save()

# register a listener for our 'lang' form
xform_received.connect(lang, dispatch_uid='lang')

def who(sender, **kwargs):
    """
    Allows users to look up their role in the system.
    """
    xform = kwargs['xform']
    submission = kwargs['submission']

    if xform.get_primary_keyword() == 'who' and not submission.has_errors:
        # see if this connection is an accountant
        acc = Accountant.objects.filter(connection=submission.connection)
        if acc:
            acc = acc[0]
            submission.template_vars['acc'] = acc
            submission.response = Blurb.get(xform, 'acc', submission.template_vars,
                                            "You are registered as an accountant for the {{ acc.wetmill.name }} wet mill.")
            return

        # otherwise a CPO perhaps?
        cpos = CPO.objects.filter(connection=submission.connection)
        if cpos:
            cpo_ids = ", ".join(["%s = %d" % (cpo.name, cpo.cpo_id) for cpo in cpos])
            submission.template_vars['cpos'] = cpo_ids
            submission.response = Blurb.get(xform, 'cpo', submission.template_vars,
                                            "You are registered as a CPO. {{ cpos }}")
            return

        # csp officer?
        csp = CSPOfficer.objects.filter(connection=submission.connection)
        if csp:
            csp = csp[0]
            submission.template_vars['csp'] = csp
            submission.response = Blurb.get(xform, 'csp', submission.template_vars,
                                            "You are registered as an officer for {{ csp.csp.name }}.")
            return

        # observer?
        obs = WetmillObserver.objects.filter(connection=submission.connection)
        if obs:
            obs = obs[0]
            submission.template_vars['obs'] = obs
            submission.response = Blurb.get(xform, 'obs', submission.template_vars,
                                            "You are registered as an observer of the {{ obs.wetmill.name }} wet mill.")
            return

        # not registered?  that's an error
        submission.has_errors = True
        submission.save()

# register a listener for our 'who' form
xform_received.connect(who, dispatch_uid='who')

def lookup(sender, **kwargs):
    """
    Allows an accountant to look up the cpo ids for his wetmill.
    """
    xform = kwargs['xform']
    submission = kwargs['submission']

    if xform.get_primary_keyword() == 'lookup' and not submission.has_errors:
        # get the accountant for this connection
        acc = submission.eav.lookup_acc

        # look up any cpos for his wet mill
        cpos = CPO.objects.filter(wetmill=acc.wetmill)
        if not cpos:
            submission.response = Blurb.get(xform, 'none', dict(),
                                            "There are no CPOs registered for this wet mill.")
        else:
            cpos = ", ".join(["%d: %s" % (cpo.cpo_id, cpo.name) for cpo in cpos])
            submission.template_vars['cpos'] = cpos
            submission.response = render(xform.response, submission.template_vars)

xform_received.connect(lookup, dispatch_uid='lookup')

def undo(sender, **kwargs):
    """
    Allows for undoing of messages.
    """
    xform = kwargs['xform']
    submission = kwargs['submission']

    if xform.get_primary_keyword() == 'undo' and not submission.has_errors:
        # look up the last message sent by this connection in the last thirty minutes
        cutoff = datetime.now() - timedelta(minutes=30)
        
        last_submission = XFormSubmission.objects.filter(created__gte=cutoff,
                                                         connection=submission.connection).order_by('-created', '-pk').exclude(id=submission.id).exclude(xform__keyword__startswith='ok')

        cancel_message = None

        # if we found a submission, see if that submission was a real SMS submission
        if last_submission:
            last_submission = last_submission[0]

            # try to find a submission that matches this message
            subs = SMSSubmission.objects.filter(submission=last_submission).order_by('-created', '-pk')
            if subs:
                cancel_message = subs[0]

        # if we found the submission, cancel it
        if cancel_message:
            # mark our raw message as having an error
            last_submission.has_errors = True
            last_submission.save()

            concrete = lookup_concrete_submission(cancel_message)
            if concrete:
                concrete.is_active = False
                concrete.save()

            # and delete our SMS submission
            cancel_message.active = False
            cancel_message.save()
            
            submission.template_vars['msg'] = last_submission
            submission.template_vars['keyword'] = last_submission.xform.get_primary_keyword()

            # did our original submission have an accountant?
            keyword = last_submission.xform.get_primary_keyword()
            accountant = getattr(last_submission.eav, '%s_accountant' % keyword, None)
            if accountant:
                submission.template_vars['accountant'] = accountant

                # send a CC to any observers that this message was removed
                send_wetmill_ccs(submission.connection, submission.xform, accountant.wetmill, submission.template_vars)

        # we couldn't find a message to cancel, tell them so
        else:
            submission.has_errors = True
            submission.save()
            submission.response = Blurb.get(xform, 'none', dict(),
                                            "No previous submission found to cancel.")

xform_received.connect(undo, dispatch_uid='undo')

class SMSSubmission(models.Model):
    """
    Abstract base class for all the stored submissions.  This lets us easily look up what was the
    last message received so we can cancel it.
    """
    submission = models.ForeignKey(XFormSubmission, null=True, blank=True, verbose_name=_("Submission"))
    day = models.DateField(auto_now_add=True, verbose_name=_("Day"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))
    active = models.BooleanField(default=True, verbose_name=_("Active"))

    created_by = models.ForeignKey(User, null=True, verbose_name=_("Created by"),
                                   help_text=_("What user created this submission if any"))


    objects = ActiveManager()
    all = models.Manager()

class StoreSubmission(SMSSubmission):
    """
    Holds the data from the 'store' command for parchment movements
    """
    accountant = models.ForeignKey(Accountant, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    daylot = models.CharField(max_length=8, help_text="Format: DD.MM.YY", verbose_name=_("Daylot"))
    gradea_moved = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Grade A Stored"))
    gradeb_moved = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Grade B Stored"))

    objects = ActiveManager()
    all = models.Manager()
    
    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - store %s %s %s" % (self.accountant.connection, self.daylot, self.gradea_moved, self.gradeb_moved)

    def get_data(self): # pragma: no cover
        return [ self.daylot, self.gradea_moved, self.gradeb_moved ]

    def get_labels(self): # pragma: no cover
        return [ "Day Lot", "Grade A Stored", "Grade B Stored" ]
        

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating a StoreSubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'store' and not submission.has_errors: # pragma: no cover
            # is a season open?
            season = get_season(country)
            if not season:
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, submission.eav.store_acc.wetmill, ['FULL']):
                return
            
            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = submission.eav.store_acc.wetmill
            
            # make sure we have cherry registered for that daylot
            cherry_deliveries = CherrySubmission.objects.filter(wetmill=submission.eav.store_acc.wetmill, daylot=submission.eav.store_dlid)
            if len(cherry_deliveries) == 0:
                submission.has_errors = True
                submission.save()
                
                submission.response = Blurb.get(xform, "unknown_daylot", submission.template_vars,
                                                "Unable to find any cherry delivered to {{ wetmill.name }} for the daylot: {{ daylot }}  Please check your daylot id.")
            else:
                # create our StoreSubmission
                sub = StoreSubmission.objects.create(submission=submission,
                                                     accountant=submission.eav.store_acc,
                                                     wetmill=submission.eav.store_acc.wetmill,
                                                     season=season,
                                                     daylot=submission.eav.store_dlid,
                                                     gradea_moved=Decimal(str(submission.eav.store_amoved)),
                                                     gradeb_moved=Decimal(str(submission.eav.store_bmoved)))

                # calculate values for our template
                values = submission.template_vars

                # total cherry for that daylot
                total_cherry = 0
                for delivery in cherry_deliveries:
                    total_cherry += delivery.cherry

                total_parchment = roundd(sub.gradea_moved + sub.gradeb_moved)

                if total_parchment > 0:
                    # calculate our cherry / parchment ratio
                    values['cherry_to_parchment'] = roundd(total_cherry / total_parchment)

                    # and grade a to total
                    values['gradea_to_parchment'] = roundd(sub.gradea_moved / total_parchment)
                else:
                    values['cherry_to_parchment'] = "0"
                    values['gradea_to_parchment'] = "0"

                # rerender our template
                submission.response = XForm.render_response(xform.response, values)

                # send off any cc's
                send_wetmill_ccs(submission.connection, xform, submission.eav.store_acc.wetmill, submission.template_vars)

# register as a listener for incoming forms
xform_received.connect(StoreSubmission.create_submission, dispatch_uid='store_submission')

class ShippingSubmission(SMSSubmission):
    """
    Holds the data from the 'send' command for shipments to csps
    """
    accountant = models.ForeignKey(Accountant, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    parchmenta_kg = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Parchment A Kgs"))
    parchmenta_bags = models.IntegerField(verbose_name="Parchment A Bags")
    parchmentb_kg = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Parchment B Kgs"))
    parchmentb_bags = models.IntegerField(verbose_name=_("Parchment B Bags"))
    license_plate = models.CharField(max_length=128, verbose_name=_("Licence Plate"))

    objects = ActiveManager()
    all = models.Manager()
    
    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - shipment on truck %s " % (self.accountant.connection, self.license_plate)

    def get_data(self): # pragma: no cover
        return [ self.parchmenta_kg, self.parchmenta_bags, self.parchmentb_kg, self.parchmentb_bags, self.license_plate ]

    def get_labels(self): # pragma: no cover
        return [ "Parchment A (kg)", "Parchment A (bags)", "Parchment B (kg)", "Parchment B (bags)", "License Plate" ]


    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating a ShippingSubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'send' and not submission.has_errors: # pragma: no cover
            # is a season open?
            season = get_season(country)
            if not season:
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, submission.eav.send_acc.wetmill, ['FULL']):
                return            
            
            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = submission.eav.send_acc.wetmill

            # create our ShippingSubmission
            sub = ShippingSubmission.objects.create(submission=submission,
                                                    accountant=submission.eav.send_acc,
                                                    wetmill=submission.eav.send_acc.wetmill,
                                                    season=season,
                                                    parchmenta_kg=str(submission.eav.send_pakg),
                                                    parchmenta_bags=submission.eav.send_pab,
                                                    parchmentb_kg=str(submission.eav.send_pbkg),
                                                    parchmentb_bags=submission.eav.send_pbb,
                                                    license_plate=submission.eav.send_license)

            # send a CC to our csp
            MessageCC.send_cc(xform, 'csp', submission.connection,
                              CSPOfficer.objects.filter(csp=sub.wetmill.get_csp()), submission.template_vars)

# register as a listener for incoming forms
xform_received.connect(ShippingSubmission.create_submission, dispatch_uid='shipping_submission')

class ReceivedSubmission(SMSSubmission):
    """
    Holds the data from the 'rec' command for shipments arriving at CSPs
    """
    officer = models.ForeignKey(CSPOfficer, verbose_name=_("Officer"))
    license_plate = models.CharField(max_length=128, verbose_name=_("License Plate"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    parchmenta_kg = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Parchmenta Kg"))
    parchmenta_bags = models.IntegerField(verbose_name=_("Parchmenta Bags"))
    parchmentb_kg = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Parchmenta Kg"))
    parchmentb_bags = models.IntegerField(verbose_name=_("Parchmenta Bags"))
    moisture_content = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Moisture Consent"))
    cupping_score = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cupping Score"))

    objects = ActiveManager()
    all = models.Manager()

    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "shipment received from truck %s " % (self.license_plate)

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating a ReceivedSubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'rec' and not submission.has_errors: # pragma: no cover
            # is a season open?
            season = get_season(country)
            if not season:
                submission.response = "No open season, please contact CSP."
                submission.has_errors = True
                submission.save()
                return

            csp = submission.eav.rec_officer.csp

            # see if we can find the license plate
            shipped = ShippingSubmission.objects.filter(season=season,
                                                        license_plate=submission.eav.rec_license,
                                                        wetmill__csp=csp).order_by('-created')

            if not shipped:
                submission.response = Blurb.get(xform, 'unknown_license', submission.template_vars,
                                                "Unable to find a shipping record for license plate: {{ license }}")
                submission.has_errors = True
                submission.save()
                return
            else:
                shipped = shipped[0]

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, shipped.wetmill, ['FULL']):
                return

            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = shipped.wetmill

            # create our ReceivedSubmission
            sub = ReceivedSubmission.objects.create(submission=submission,
                                                    officer=submission.eav.rec_officer,
                                                    wetmill=shipped.wetmill,
                                                    season=season,
                                                    parchmenta_kg=str(submission.eav.rec_pakg),
                                                    parchmenta_bags=submission.eav.rec_pab,
                                                    parchmentb_kg=str(submission.eav.rec_pbkg),
                                                    parchmentb_bags=submission.eav.rec_pbb,
                                                    license_plate=submission.eav.rec_license,
                                                    moisture_content=str(submission.eav.rec_moisture),
                                                    cupping_score=str(submission.eav.rec_score))

            # rerender our template
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            # send a CC to our accountant
            MessageCC.send_cc(xform, 'acc', submission.connection,
                              Accountant.objects.filter(wetmill=sub.wetmill), submission.template_vars)

# register as a listener for incoming forms
xform_received.connect(ReceivedSubmission.create_submission, dispatch_uid='received_submission')

class CashSubmission(SMSSubmission):
    """
    Holds the data from the 'cash' command for ledger entries
    """
    accountant = models.ForeignKey(Accountant, verbose_name=_("accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    working_capital = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Working Capital"))
    income = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Income"))
    cash_advances = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cash Advances"))
    salaries = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Salaries"))
    site_collector_wages = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Site Collector Wages"))
    cherry_transport_wages = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cherry Transport Wages"))
    casual_wages = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Casual Wages"))
    other_cash_out = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Other Cash Out"))

    objects = ActiveManager()
    all = models.Manager()

    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - cash (income: %s)" % (self.accountant.connection, self.income)

    def get_data(self): # pragma: no cover
        return [ self.working_capital, self.income, self.cash_advances, self.salaries, self.site_collector_wages,
                 self.cherry_transport_wages, self.casual_wages, self.other_cash_out, self.balance() ]

    def get_labels(self): # pragma: no cover
        return [ "Working Capital", "Income", "Cash Advances", "Salaries", "Site Collector", "Transport", "Casual Wages", "Other Cash", "Balance" ]
        
    def non_cherry_expenses(self): # pragma: no cover
        """
        Returns the total of non-cherry expenses.
        """
        return self.salaries + self.site_collector_wages + self.cherry_transport_wages + self.casual_wages + self.other_cash_out

    def cash_in(self): # pragma: no cover
        """
        All the money that came in.
        """
        return self.working_capital + self.income

    def cash_out(self): # pragma: no cover
        """
        All the money that went out.
        """
        return self.cash_advances + self.site_collector_wages + self.cherry_transport_wages + self.casual_wages + self.other_cash_out

    def balance(self): # pragma: no cover
        """
        Calculates the cash balance based on our cash reports for this report.
        """
        totals = CashSubmission.objects.filter(wetmill=self.wetmill,
                                               season=self.season).filter(created__lte=self.created).aggregate(
            Sum('working_capital'), Sum('income'), Sum('cash_advances'), Sum('salaries'),
            Sum('site_collector_wages'), Sum('cherry_transport_wages'), Sum('casual_wages'),
            Sum('other_cash_out'))

        # figure out current balance from all those totals
        total_in = totals['working_capital__sum'] + totals['income__sum']
        total_out = totals['cash_advances__sum'] + totals['salaries__sum'] + totals['site_collector_wages__sum'] +  totals['cherry_transport_wages__sum'] + totals['casual_wages__sum'] + totals['other_cash_out__sum']

        return roundd(total_in - total_out, "1")

    @staticmethod
    def create_submission(sender, **kwargs): # pragma: no cover
        """
        Our XForms Signal hook for creating a CashSubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'cash' and not submission.has_errors:
            wetmill = submission.eav.cash_acc.wetmill
            
            # is a season open?
            season = get_season(country)
            if not season: 
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, submission.eav.cash_acc.wetmill, ['FULL']):
                return
            
            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = submission.eav.cash_acc.wetmill
            
            # create our CashSubmission
            sub = CashSubmission.objects.create(submission=submission,
                                                accountant=submission.eav.cash_acc,
                                                wetmill=wetmill,
                                                season=season,
                                                working_capital=Decimal(str(submission.eav.cash_wcap)),
                                                income=Decimal(str(submission.eav.cash_income)),
                                                cash_advances=Decimal(str(submission.eav.cash_advances)),
                                                salaries=Decimal(str(submission.eav.cash_salaries)),
                                                site_collector_wages=Decimal(str(submission.eav.cash_scwages)),
                                                cherry_transport_wages=Decimal(str(submission.eav.cash_transwages)),
                                                casual_wages=Decimal(str(submission.eav.cash_casualwages)),
                                                other_cash_out=Decimal(str(submission.eav.cash_cashout)))

            # do some calculations on totals
            submission.template_vars['tot_cout'] = roundd(sub.cash_advances + sub.salaries + sub.site_collector_wages + sub.cherry_transport_wages + sub.casual_wages + sub.other_cash_out, "1")

            submission.template_vars['tot_cin'] = roundd(sub.working_capital + sub.income, "1")

            # figure out our cash balance
            submission.template_vars['balance'] = sub.balance()

            # figure out the discrepency between what they said they spent and the total they paid in cherry
            # adding up all the values since the last cash report
            now = datetime.now(pytz.utc)
            local = now.astimezone(pytz.timezone(settings.USER_TIME_ZONE))

            # change our time to be 20, anything after that is probably for the current week
            end = local.replace(hour=20)
            start = end - timedelta(days=7)

            # find out how much we spent in that time on cherries
            cash_advances = Decimal(0)
            for cherry in CherrySubmission.objects.filter(wetmill=wetmill, season=season,
                                                          created__gte=start.astimezone(pytz.utc).replace(tzinfo=None),
                                                          created__lte=end.astimezone(pytz.utc).replace(tzinfo=None)):
                cash_advances += cherry.cash_advance

            # figure out what the discrepency
            submission.template_vars['advance_disc'] = roundd(Decimal(sub.cash_advances) - cash_advances, "1")
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            # send off any cc's
            send_wetmill_ccs(submission.connection, xform, submission.eav.cash_acc.wetmill, submission.template_vars)            
            
# register as a listener for incoming forms
xform_received.connect(CashSubmission.create_submission, dispatch_uid='cash_submission')

def get_day(utc_time): # pragma: no cover
    """
    Given the passed in time, returns the day that this message is referring to.
    """
    tzname = settings.USER_TIME_ZONE
    tz = pytz.timezone(tzname)

    # change the passed in date to 'local' time for this site
    local = utc_time.astimezone(tz)

    # if it is before 4, for previous day
    if local.hour < 16: # pragma: no cover
        local = local - timedelta(days=1)
    # otherwise, today is the day!
    else:
        pass

    return local.date()

def get_daylot(utc_time):
    """
    Gets the daylot based on the current time.  If it is before 4 PM, then we assume
    the report is for the previous day, otherwise, it is for today.

    The time passed in should be in UTC, ie build via:

            time = datetime.now(pytz.utc)
    """
    tzname = settings.USER_TIME_ZONE
    tz = pytz.timezone(tzname)

    # change the passed in date to 'local' time for this site
    local = utc_time.astimezone(tz)

    # if it is before 8, for previous day
    if local.hour < 20:
        local = local - timedelta(days=1)
    # otherwise, today is the day!
    else:
        pass

    return local.strftime("%d.%m.%y")

def get_deadline_for_daylot(daylot): # pragma: no cover
    """
    Returns the time submissions must have been made by for them to be marked as belonging
    to the passed in daylot.
    """
    match = re.match("^(\d{1,2})\.(\d{1,2})\.(\d\d)\.?$", daylot, re.IGNORECASE)

    if match:
        deadline = datetime(day=int(match.group(1)), month=int(match.group(2)), year=2000+int(match.group(3)),
                            tzinfo=pytz.timezone(settings.USER_TIME_ZONE))
        deadline = deadline + timedelta(days=1)
        deadline.replace(hour=20)

        # convert to utc time and strip off the tzinfo, returning it
        return deadline.astimezone(pytz.utc).replace(tzinfo=None)
    else:
        return None

def datetime_for_daylot(daylot):
    """
    Returns a datetime object in UTC for the passed in daylot
    """
    match = re.match("^(\d{1,2})\.(\d{1,2})\.(\d\d)\.?$", daylot, re.IGNORECASE)

    if match:
        deadline = datetime(day=int(match.group(1)), month=int(match.group(2)), year=(2000 + int(match.group(3))),
                            hour=0, minute=0, second=0,
                            tzinfo=pytz.utc)
        return deadline
    else: # pragma: no cover
        return None

class CherrySubmission(SMSSubmission):
    """
    Holds the data from the 'cherry' command for cpo deliveries
    """
    accountant = models.ForeignKey(Accountant, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    cpo = models.ForeignKey(CPO, verbose_name=_("CPO"))
    daylot = models.CharField(max_length=8, help_text="Format: DD.MM.YY", verbose_name=_("Daylot"))
    cash_price = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cash Price"))
    credit_price = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Credit Price"))
    cherry = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cherry"))
    cash_advance = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cash Advance"))
    credit_paid_off = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cherry Paid Off"))
    cherry_paid_cash = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cherry Paid Cash"))
    cherry_paid_credit = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cherry Paid Credit"))

    objects = ActiveManager()
    all = models.Manager()
    
    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - cherry (cpo: %s)" % (self.accountant.connection, self.cpo)

    def get_data(self): # pragma: no cover
        return [ self.cpo, self.daylot, self.cash_price, self.credit_price, self.cherry, self.cash_advance,
                 self.credit_paid_off, self.cherry_paid_cash, self.cherry_paid_credit ]

    def get_labels(self): # pragma: no cover
        return ["CPO", "Day Lot", "Cash Price", "Credit Price", "Cherry", "Cash Advance", "Credit Paid", "Cherry Cash", "Cherry Credit"]

    def get_weighted_price(self):
        """
        Returns the weighted price of cherry for this transaction.  This basically finds the average
        between the credit and cash price, though weighted by volume
        """
        total_spent = self.cherry_paid_cash + self.cherry_paid_credit
        if total_spent > Decimal(0):
            return self.cash_price * (self.cherry_paid_cash / total_spent) + self.credit_price * (self.cherry_paid_credit / total_spent)
        else: # pragma: no cover
            return (self.cash_price + self.credit_price) / 2

    def get_bought_kilos(self): # pragma: no cover
        """
        Returns how much cherry SHOULD have been bought given the prices and paid amounts sent in.
        """
        return self.cherry_paid_cash / self.cash_price + self.cherry_paid_credit / self.credit_price

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating a CherrySubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'cherry' and not submission.has_errors:
            # is a season open?
            season = get_season(country)
            if not season: # pragma: no cover
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, submission.eav.cherry_acc.wetmill, ['FULL']): # pragma: no cover
                return            
            
            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = submission.eav.cherry_acc.wetmill
            
            # create our cherry submission
            sub = CherrySubmission.objects.create(submission=submission,
                                                  accountant=submission.eav.cherry_acc,
                                                  wetmill=submission.eav.cherry_acc.wetmill,
                                                  season=season,
                                                  daylot=get_daylot(datetime.now(pytz.utc)),
                                                  cpo=submission.eav.cherry_cpo,
                                                  cash_price=str(submission.eav.cherry_cash_price),
                                                  credit_price=str(submission.eav.cherry_credit_price),
                                                  cherry=str(submission.eav.cherry_cherry),
                                                  cash_advance=str(submission.eav.cherry_cash_advance),
                                                  credit_paid_off=str(submission.eav.cherry_credit_paid_off),
                                                  cherry_paid_cash=str(submission.eav.cherry_cherry_cash),
                                                  cherry_paid_credit=str(submission.eav.cherry_cherry_credit))

            # build up how much this cpo has gotten from a wetmill
            running_total = CherrySubmission.objects.filter(cpo=sub.cpo, season=sub.season).aggregate(
                Sum('cash_advance'), Sum('credit_paid_off'), Sum('cherry_paid_credit'), Sum('cherry_paid_cash'))

            # build up an aggregate of repayments
            repayments = ReturnSubmission.objects.filter(cpo=sub.cpo, season=sub.season).aggregate(Sum('cash'))
            if not repayments['cash__sum']:
                repayments = dict(cash__sum=Decimal(0))

            # cash balance is going to be the cash advance - cherry_paid_cash
            submission.template_vars['cash_b'] = roundd(running_total['cash_advance__sum'] - running_total['cherry_paid_cash__sum'] - repayments['cash__sum'], "1")

            # credit balance is how much credit they have handed out - how much they have paid off
            submission.template_vars['credit_b'] = roundd(running_total['cherry_paid_credit__sum'] - running_total['credit_paid_off__sum'], "1")

            # total values of missing coffee can only be calculated by iterating all entries
            total_value = 0
            total_paid = 0
            for cherry in CherrySubmission.objects.filter(cpo=sub.cpo, season=sub.season):
                total_value += (cherry.get_weighted_price() * cherry.cherry)
                total_paid += cherry.cherry_paid_cash + cherry.cherry_paid_credit

            submission.template_vars['missing_cv'] = roundd(total_paid - total_value, 1)
            submission.template_vars['daylot'] = sub.daylot

            # rerender our response with our new values
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            # send off our CC to the cpo
            MessageCC.send_cc(xform, 'cpo', submission.connection, [sub.cpo], submission.template_vars)

            # and any others
            send_wetmill_ccs(submission.connection, xform, submission.eav.cherry_acc.wetmill, submission.template_vars)            
            
# register as a listener for incoming forms
xform_received.connect(CherrySubmission.create_submission, dispatch_uid='cherry_submission')

class ReturnSubmission(SMSSubmission):
    """
    Holds the data from a 'return' message, which is used when a CPO pays back any left over
    advance.
    """
    accountant = models.ForeignKey(Accountant, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    cpo = models.ForeignKey(CPO, verbose_name=_("CPO"))
    cash = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cash"))

    objects = ActiveManager()
    all = models.Manager()
    
    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - return (cpo: %s)" % (self.accountant.connection, self.cpo)

    def get_data(self): # pragma: no cover
        return [ self.cpo, self.cash ]

    def get_labels(self): # pragma: no cover
        return [ "CPO", "Cash" ]

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating a Return Submission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'return' and not submission.has_errors: # pragma: no cover
            # is a season open?
            season = get_season(country)
            if not season:
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, submission.eav.return_acc.wetmill, ['FULL']):
                return            
            
            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = submission.eav.return_acc.wetmill
            
            # create our submission
            sub = ReturnSubmission.objects.create(submission=submission,
                                                  accountant=submission.eav.return_acc,
                                                  wetmill=submission.eav.return_acc.wetmill,
                                                  season=season,
                                                  cpo=submission.eav.cpo,
                                                  cash=submission.eav.return_cash)

            # build up how much this cpo has gotten from a wetmill
            running_total = CherrySubmission.objects.filter(cpo=sub.cpo, season=sub.season).aggregate(
                Sum('cash_advance'), Sum('credit_paid_off'), Sum('cherry_paid_credit'), Sum('cherry_paid_cash'))

            # build up an aggregate of repayments
            repayments = ReturnSubmission.objects.filter(cpo=sub.cpo, season=sub.season).aggregate(Sum('cash'))

            # cash balance is going to be the cash advance - credit_paid off - cherry_paid_cash
            submission.template_vars['cash_b'] = running_total['cash_advance__sum'] - running_total['cherry_paid_cash__sum'] - repayments['cash__sum']

            # credit balance is how much credit they have handed out - how much they have paid off
            submission.template_vars['credit_b'] = running_total['cherry_paid_credit__sum'] - running_total['credit_paid_off__sum']

            # total values of missing coffee can only be calculated by iterating all entries
            total_value = 0
            total_paid = 0
            for cherry in CherrySubmission.objects.filter(cpo=sub.cpo, season=sub.season):
                total_value += (cherry.get_weighted_price() * cherry.cherry)
                total_paid += cherry.cherry_paid_cash + cherry.cherry_paid_credit

            submission.template_vars['missing_cv'] = roundd(total_paid - total_value, "1")

            # rerender our response with our new values
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            # send off our CC to the cpo
            MessageCC.send_cc(xform, 'cpo', submission.connection, [sub.cpo], submission.template_vars)

            # send off our CCs
            send_wetmill_ccs(submission.connection, xform, submission.eav.return_acc.wetmill, submission.template_vars)            
            
# register as a listener for incoming forms
xform_received.connect(ReturnSubmission.create_submission, dispatch_uid='return_submission')

# register a new type for day lot id, which is really just a date
def parse_daylot(command, value, today=None, raw=None, connection=None):
    if not today:
        today = datetime.now().date()

    day = None
    form = XForm.objects.get(keyword__startswith='ibitumbwe')

    # full date, including year
    match = re.match("^(\d{1,2})[\.,\/](\d{1,2})[\.,\/](\d{2,4})\.?$", value, re.IGNORECASE)
    if match:
        day_of_month = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))

        # add 2000 to dates that are two digit
        if year < 100:
            year += 2000

        try:
            day = date(day=day_of_month, month=month, year=year)
        except:
            raise ValidationError(Blurb.get(form, 'invalid_day', dict(value=value),
                                            "Error. The day you specified is not valid, format is DD.MM, ie: 24.03 was {{ value }}"))

    if not day:
        # no year
        match = re.match("^(\d{1,2})[\.,/](\d{1,2})\.?$", value, re.IGNORECASE)
        if match:
            day_of_month = int(match.group(1))
            month = int(match.group(2))

            try:
                day = date(day=day_of_month, month=month, year=today.year)

                if day > today:
                    day = date(day=day_of_month, month=month, year=today.year - 1)
            except:
                raise ValidationError(Blurb.get(form, 'invalid_day', dict(value=value),
                                                "Error. The day you specified is not valid, format is DD.MM, ie: 24.03 was {{ value }}"))

    if not day:
        raise ValidationError(Blurb.get(form, 'bad_day_format', dict(value=value),
                                        "Error. Invalid day format, format is DD.MM, ie: 24.03 was {{ value }}"))

    # can't be in the future
    if day > today:
        raise ValidationError(Blurb.get(form, 'future_day', dict(value=value),
                                        "Error. The day you specified is in the future, please resend with a valid date."))


    country = get_country_for_backend(connection.backend.name)

    # can't be too long ago, we use the season date as our judge
    from dashboard.models import Assumptions
    season = get_season(country)
    season_assumptions = Assumptions.get_or_create(season, None, None, User.objects.get(pk=-1))

    if (day - season_assumptions.season_end).days > 60:
        raise ValidationError(Blurb.get(form, 'future_season_day', dict(value=value),
                                        "Error. The day you specified is too far past the season end date.  Please resend with a valid date."))

    if (season_assumptions.season_start - day).days > 30:
        raise ValidationError(Blurb.get(form, 'past_day', dict(value=value),
                                        "Error. The day you specified is too far in the past, please resend with a valid date."))

    return "%02d.%02d.%02d" % (day.day, day.month, day.year % 100)

XFormField.register_field_type('daylot', 'Day Lot', parse_daylot,
                               xforms_type='string', db_type=XFormField.TYPE_TEXT)

class SummarySubmission(SMSSubmission):
    """
    Holds the data from the 'sum' command for cpo deliveries
    """
    accountant = models.ForeignKey(Accountant, verbose_name=_("Accontant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    daylot = models.CharField(max_length=8, verbose_name=_("Daylot"))
    cherry = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cherry"))
    paid = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Paid"))
    stored = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Stored"))
    sent = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Sent"))
    balance = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Balance"))

    objects = ActiveManager()
    all = models.Manager()
    
    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - summary (wetmill: %s)" % (self.accountant.connection, self.wetmill.name)

    def get_data(self): # pragma: no cover
        return [self.daylot, self.cherry, self.paid, self.stored, self.sent, self.balance]

    def get_labels(self): # pragma: no cover
        return ["Day Lot", "Cherry Collected", "Total Paid", "Parchment to Store", "Parchment to CSP", "Cash Balance"]

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating a SummarySubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)

        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'sum' and not submission.has_errors:
            # is a season open?
            season = get_season(country)
            if not season: # pragma: no cover
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, submission.eav.sum_acc.wetmill, ['LITE']): # pragma: no cover
                return            

            # create our cherry submission
            sub = SummarySubmission.objects.create(submission=submission,
                                                   accountant=submission.eav.sum_acc,
                                                   wetmill=submission.eav.sum_acc.wetmill,
                                                   season=season,
                                                   daylot=get_daylot(datetime.now(pytz.utc)),
                                                   cherry=Decimal(str(submission.eav.sum_cherry)),
                                                   paid=Decimal(str(submission.eav.sum_paid)),
                                                   stored=Decimal(str(submission.eav.sum_stored)),
                                                   sent=Decimal(str(submission.eav.sum_sent)),
                                                   balance=Decimal(str(submission.eav.sum_balance)))
                                                   

            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = sub.wetmill
            submission.template_vars['daylot'] = sub.daylot

            # average price paid
            if sub.cherry > 0:
                submission.template_vars['avg_price'] = roundd(sub.paid / sub.cherry, ".1")
            else: # pragma: no cover
                submission.template_vars['avg_price'] = 0

            # re render our response with our new values
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            # send any cc's for this message
            send_wetmill_ccs(submission.connection, xform, sub.wetmill, submission.template_vars)            
            
# register as a listener for incoming forms
xform_received.connect(SummarySubmission.create_submission, dispatch_uid='summary_submission')

def get_week_start_before(today):
    # normalize to friday or previous friday (if saturday or monday)
    day_shift = 7

    if today.weekday() < 4:
        day_shift += (today.weekday() + 3)

    elif today.weekday() > 4:
        day_shift += (today.weekday() - 4)

    return today - timedelta(days=day_shift)

def get_week_start_during(today):
    # normalize to friday or previous friday (if saturday or monday)
    day_shift = 0
    if today.weekday() < 4:
        day_shift += (today.weekday() + 3)

    elif today.weekday() > 4: # pragma: no cover
        day_shift += (today.weekday() - 4)

    return today - timedelta(days=day_shift)

def to_decimal(decimal_string):
    # removes commas from the passed in string then casts it to a Decimal
    return Decimal(decimal_string.replace(',',''))

class AmafarangaSubmission(SMSSubmission):
    accountant = models.ForeignKey(Accountant, null=True, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    start_of_week = models.DateField(verbose_name=_("Start of Week"),
                                     help_text=_("The day the period for this report began. (weeks start on Fridays)"))
    opening_balance = models.DecimalField(verbose_name=_("Opening Balance"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("The opening balance at this wetmill for the week"))
    working_capital = models.DecimalField(verbose_name=_("Working Capital"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("The total working capital received"))
    other_income = models.DecimalField(verbose_name=_("Other Income"),
                                       max_digits=16, decimal_places=2,
                                       help_text=_("Total of other income received"))
    advanced = models.DecimalField(verbose_name=_("Advanced"),
                                   max_digits=16, decimal_places=2,
                                   help_text=_("Total cash advanced to sites"))
    full_time_labor = models.DecimalField(verbose_name=_("Full Time Labor"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Total full time labor expenses"))
    casual_labor = models.DecimalField(verbose_name=_("Casual Labor"),
                                       max_digits=16, decimal_places=2,
                                       help_text=_("Total casual labor expenses"))
    commission = models.DecimalField(verbose_name=_("Commission"),
                                     max_digits=16, decimal_places=2,
                                     help_text=_("Total site collection commission paid"))
    transport = models.DecimalField(verbose_name=_("Transport"),
                                    max_digits=16, decimal_places=2,
                                    help_text=_("Total cherry transport costs incurred"))
    other_expenses = models.DecimalField(verbose_name=_("Other Expenses"),
                                         max_digits=16, decimal_places=2,
                                         help_text=_("Total other expenses this week"))

    is_active = models.BooleanField(verbose_name=_("Is Active"),
                                    default=False,
                                    help_text=_("Whether this submission is active"))

    objects = ActiveManager()
    all = models.Manager()

    EXPORT_FIELDS = (dict(label=_("Wetmill"), field='wetmill'),
                     dict(label=_("Week Starting"), field='start_of_week'),
                     dict(label=_("Opening Balance"), field='opening_balance', currency=True),
                     dict(label=_("Working Capital"), field='working_capital', currency=True),
                     dict(label=_("Other Income"), field='other_income', currency=True),
                     dict(label=_("Advanced"), field='advanced', currency=True),
                     dict(label=_("Full Time Labor"), field='full_time_labor', currency=True),
                     dict(label=_("Casual Labor"), field='casual_labor', currency=True),
                     dict(label=_("Commission"), field='commission', currency=True),
                     dict(label=_("Transport"), field='transport', currency=True),
                     dict(label=_("Other Expenses"), field='other_expenses', currency=True))

    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - amafaranga" % (self.wetmill.name,)

    def get_data(self): # pragma: no cover
        calculated = self.get_calculated_values()

        data = []
        data.append(dict(value=self.start_of_week, display_class='date'))
        data.append(dict(value=self.opening_balance))
        data.append(dict(value=self.working_capital, total=True))
        data.append(dict(value=self.other_income, total=True))
        data.append(dict(value=self.advanced, total=True))
        data.append(dict(value=self.full_time_labor, total=True))
        data.append(dict(value=self.casual_labor, total=True))
        data.append(dict(value=self.commission, total=True))
        data.append(dict(value=self.transport, total=True))
        data.append(dict(value=self.other_expenses, total=True))
        data.append(dict(value=calculated['closing_balance'], display_class='calculated'))
        data.append(dict(value=calculated['variance'], display_class='calculated'))

        if self.submission:
            data.append(dict(value=self.submission.created, display_class='date'))

        return data

    def get_labels(self): # pragma: no cover
        return [ "Start of Week", "Opening Balance", "Working Capital", "Income", "Advanced", "Full Time Labor", "Casual Labor",
                 "Commission", "Transport", "Other Expenses", "Closing Balance", "Variance", "Submitted" ]

    def get_closing_balance(self):
        return self.opening_balance + self.working_capital + self.other_income - self.advanced - \
               self.full_time_labor - self.casual_labor - self.commission - self.transport - \
               self.other_expenses
        
    def get_calculated_values(self):
        calculated = dict()

        # get the submission for our previous week
        previous_start = self.start_of_week - timedelta(days=7)
        previous = AmafarangaSubmission.objects.filter(wetmill=self.wetmill, start_of_week=previous_start)
        previous_closing = None
        if previous:
            previous_closing = comma_formatted(previous[0].get_closing_balance(), False)

        calculated['opening_balance'] = comma_formatted(self.opening_balance, False)
        calculated['cash_inflow'] = comma_formatted(self.working_capital+self.other_income, False)
        calculated['cash_outflow'] = comma_formatted(self.advanced + self.full_time_labor + self.casual_labor + 
                                                     self.commission + self.transport + self.other_expenses, False)
        calculated['closing_balance'] = comma_formatted(self.get_closing_balance(), False)

        calculated['week_start'] = self.start_of_week.strftime("%d.%m.%y")
        calculated['week_end'] = (self.start_of_week + timedelta(days=6)).strftime("%d.%m.%y")

        if not previous_closing is None:
            calculated['variance'] = comma_formatted(to_decimal(previous_closing) - to_decimal(calculated['opening_balance']), False)
        else:
            calculated['variance'] = "0"

        return calculated

    def confirm(self):
        """
        Called when this message is confirmed
        """
        template_vars = self.get_calculated_values()
        template_vars['wetmill'] = self.wetmill

        AmafarangaSubmission.objects.filter(wetmill=self.wetmill, start_of_week=self.start_of_week).exclude(id=self.pk).update(active=False, is_active=False)

        # send off any cc's
        send_wetmill_ccs(self.submission.connection, self.submission.xform, self.wetmill, template_vars)            

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating an AmafarangaSubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'amafaranga' and not submission.has_errors:
            wetmill = submission.eav.amafaranga_accountant.wetmill

            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = wetmill
            
            # is a season open?
            season = get_season(country)
            if not season: # pragma: no cover
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, wetmill, ['2012']):
                return

            # what week is this for
            week_start = get_week_start_during(datetime_for_daylot(submission.eav.amafaranga_date).date())

            # if this week isn't yet over, that is an error
            if week_start + timedelta(days=7) > datetime.now().date():
                submission.has_errors = True
                submission.response = Blurb.get(submission.xform, 'future_submission', dict(),
                                                "You cannot submit an amafaranga submission for a week that is not yet complete, specify the starting date of the week for amafaranga messages")
                return

                # create our Amafaranga Submission, they start off as NOT active
            sub = AmafarangaSubmission.objects.create(submission=submission,
                                                      active=False,
                                                      start_of_week=week_start,
                                                      accountant=submission.eav.amafaranga_accountant,
                                                      wetmill=wetmill,
                                                      season=season,
                                                      opening_balance=Decimal(str(submission.eav.amafaranga_opening_balance)),
                                                      working_capital=Decimal(str(submission.eav.amafaranga_working_capital)),
                                                      other_income=Decimal(str(submission.eav.amafaranga_other_income)),
                                                      advanced=Decimal(str(submission.eav.amafaranga_advanced)),
                                                      full_time_labor=Decimal(str(submission.eav.amafaranga_full_time_labor)),
                                                      casual_labor=Decimal(str(submission.eav.amafaranga_casual_labor)),
                                                      commission=Decimal(str(submission.eav.amafaranga_commission)),
                                                      transport=Decimal(str(submission.eav.amafaranga_transport)),
                                                      other_expenses=Decimal(str(submission.eav.amafaranga_other_expenses)))

            # do our calculations and stuff them in our template
            submission.template_vars.update(sub.get_calculated_values())
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            approve_submission.apply_async(args=[sub, AmafarangaSubmission], countdown=ONE_HOUR)
            
# register as a listener for incoming forms
xform_received.connect(AmafarangaSubmission.create_submission, dispatch_uid='amafaranga_submission')

def getd(dictionary, key):
    if not key in dictionary or not dictionary[key]:
        return Decimal(0)
    else:
        return dictionary[key]

class IbitumbweSubmission(SMSSubmission):
    accountant = models.ForeignKey(Accountant, null=True, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    report_day = models.DateField(null=False, verbose_name=_("Report Day"))
    cash_advanced = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cash Advanced"),
                                        help_text=_("The total cash advanced to sites on this day"))
    cash_returned = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cash Returned"),
                                        help_text=_("The total cash returned from sites on this day"))
    cash_spent = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cash Spent"),
                                     help_text=_("Total of cash spent on cherry by all sites"))
    credit_spent = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Credit Spent"),
                                       help_text=_("Total of credit spent on cherry by all sites"))
    cherry_purchased = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Cherry Purchased"),
                                           help_text=_("The total cherry purchased today at all sites"))
    credit_cleared = models.DecimalField(max_digits=16, decimal_places=2, null=True, verbose_name=_("Credit Cleared"),
                                         help_text=_("Total credit cleared with cash today"))

    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"),
                                    help_text=_("Whether this submission is active"))

    objects = ActiveManager()
    all = models.Manager()

    EXPORT_FIELDS = (dict(label=_("Wetmill"), field='wetmill'),
                     dict(label=_("Day"), field='report_day'),
                     dict(label=_("Cash Advanced"), field='cash_advanced', currency=True),
                     dict(label=_("Cash Returned"), field='cash_returned', currency=True),
                     dict(label=_("Cash Spent"), field='cash_spent', currency=True),
                     dict(label=_("Credit Spent"), field='credit_spent', currency=True),
                     dict(label=_("Cherry Purchased"), field='cherry_purchased', weight=True),
                     dict(label=_("Credit Cleared"), field='credit_cleared', currency=True))

    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - ibitumbwe" % (self.wetmill.name,)

    def get_data(self): # pragma: no cover
        data = []

        calculated = self.get_calculated_values()

        data.append(dict(value=self.report_day, display_class='date'))
        data.append(dict(value=self.cash_advanced, total=True))
        data.append(dict(value=self.cash_returned, total=True))
        data.append(dict(value=self.cash_spent, total=True))
        data.append(dict(value=self.credit_spent, total=True))
        data.append(dict(value=self.cherry_purchased, total=True))

        data.append(dict(value=calculated['cherry_price'], display_class='calculated'))
        data.append(dict(value=calculated['cash_balance'], display_class='calculated'))

        if self.submission:
            data.append(dict(value=self.submission.created, display_class='date'))

        return data

    def get_labels(self): # pragma: no cover
        return [ "Day", "Cash Advanced", "Cash Returned", "Cash Spent", "Credit Spent", "Cherry Purchased", "Cherry Price", "Cash Balance", "Submitted" ]

    def get_calculated_values(self):
        calculated = dict()
        has_decimals = self.wetmill.country.currency.has_decimals

        cherry_price = Decimal(0)
        if self.cherry_purchased > Decimal(0):
            cherry_price = comma_formatted(((self.cash_spent + self.credit_spent) / self.cherry_purchased) + Decimal(".5"), has_decimals)

        calculated['cherry_price'] = cherry_price

        totals = IbitumbweSubmission.objects.filter(wetmill=self.wetmill, season=self.season, report_day__lte=self.report_day, created__lte=self.created).aggregate(
            Sum('cash_advanced'), Sum('cash_returned'), Sum('cash_spent'), Sum('credit_spent'), Sum('credit_cleared'))
        
        cash_balance = getd(totals, 'cash_advanced__sum') - getd(totals, 'cash_returned__sum') - getd(totals, 'cash_spent__sum') - getd(totals, 'credit_spent__sum')

        if not self.active:
            cash_balance = cash_balance + self.cash_advanced - self.cash_returned - self.cash_spent - self.credit_spent

        calculated['cash_balance'] = comma_formatted(cash_balance, has_decimals)

        calculated['cherry_purchased'] = comma_formatted(self.cherry_purchased, True)
        calculated['wetmill'] = self.wetmill
        calculated['day'] = self.report_day.strftime("%d.%m.%y")

        return calculated

    def confirm(self):
        """
        Called when this message is confirmed
        """
        template_vars = self.get_calculated_values()
        template_vars['wetmill'] = self.wetmill

        # make any other ibitumbwe or twakinze submissions on this date inactive
        IbitumbweSubmission.objects.filter(wetmill=self.wetmill, report_day=self.report_day).exclude(id=self.pk).update(active=False, is_active=False)
        TwakinzeSubmission.objects.filter(wetmill=self.wetmill, report_day=self.report_day).update(active=False, is_active=False)

        # send off any cc's
        send_wetmill_ccs(self.submission.connection, self.submission.xform, self.wetmill, template_vars)            

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating an IbitumbweSubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'ibitumbwe' and not submission.has_errors:

            cherry_purchased = from_country_weight(submission.eav.ibitumbwe_cherry_purchased, country)

            wetmill = submission.eav.ibitumbwe_accountant.wetmill

            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = wetmill
            
            # is a season open?
            season = get_season(country)
            if not season: # pragma: no cover
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, wetmill, ['2012']):
                return


            # what day this is for
            day = datetime_for_daylot(submission.eav.ibitumbwe_date).date()

            # create our Amafaranga Submission, they start off as NOT active
            sub = IbitumbweSubmission.objects.create(submission=submission,
                                                     active=False,
                                                     report_day=day,
                                                     accountant=submission.eav.ibitumbwe_accountant,
                                                     wetmill=wetmill,
                                                     season=season,
                                                     cash_advanced=Decimal(str(submission.eav.ibitumbwe_cash_advanced)),
                                                     cash_returned=Decimal(str(submission.eav.ibitumbwe_cash_returned)),
                                                     cash_spent=Decimal(str(submission.eav.ibitumbwe_cash_spent)),
                                                     credit_spent=Decimal(str(submission.eav.ibitumbwe_credit_spent)),
                                                     cherry_purchased=cherry_purchased)

            # do our calculations and stuff them in our template
            submission.template_vars.update(sub.get_calculated_values())
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            approve_submission.apply_async(args=[sub, IbitumbweSubmission], countdown=ONE_HOUR)


    @staticmethod
    def create_day_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating an IbitumbweSubmission submitted using the 'day' form
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)

        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'day' and not submission.has_errors:
            wetmill = submission.eav.day_accountant.wetmill

            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = wetmill

            # is a season open?
            season = get_season(country)
            if not season: # pragma: no cover
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, wetmill, ['LIT2']):
                return

            # what day this is for
            day = datetime_for_daylot(submission.eav.day_date).date()

            # create our Submission, they start off as NOT active
            sub = IbitumbweSubmission.objects.create(submission=submission,
                                                     active=False,
                                                     report_day=day,
                                                     accountant=submission.eav.day_accountant,
                                                     wetmill=wetmill,
                                                     season=season,
                                                     cash_advanced=Decimal(0),
                                                     cash_returned=Decimal(0),
                                                     cash_spent=Decimal(0),
                                                     credit_spent=Decimal(0),
                                                     cherry_purchased=Decimal(str(submission.eav.day_cherry_purchased)))

            # do our calculations and stuff them in our template
            submission.template_vars.update(sub.get_calculated_values())
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            approve_submission.apply_async(args=[sub, IbitumbweSubmission], countdown=ONE_HOUR)
            
# register as a listener for incoming forms
xform_received.connect(IbitumbweSubmission.create_submission, dispatch_uid='ibitumbwe_submission')
xform_received.connect(IbitumbweSubmission.create_day_submission, dispatch_uid='ibitumbwe_day_submission')

class SitokiSubmission(SMSSubmission):
    accountant = models.ForeignKey(Accountant, null=True, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    start_of_week = models.DateField(verbose_name=_("Start of Week"),
                                     help_text=_("The day the period for this report began. (weeks start on Fridays)"))
    grade_a_stored = models.DecimalField(verbose_name=_("Grade A Stored"),
                                         max_digits=16, decimal_places=2,
                                         help_text=_("Total A grade parchment moved to store in the past week"))
    grade_b_stored = models.DecimalField(verbose_name=_("Grade B Stored"),
                                         max_digits=16, decimal_places=2,
                                         help_text=_("Total B grade parchment moved to store in the past week"))
    grade_c_stored = models.DecimalField(verbose_name=_("Grade C Stored"),
                                         max_digits=16, decimal_places=2,
                                         help_text=_("Total C grade parchment moved to store in the past week"))
    grade_a_shipped = models.DecimalField(verbose_name=_("Grade A Shipped"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Total A grade parchment shipped to store in the past week"))
    grade_b_shipped = models.DecimalField(verbose_name=_("Grade B Shipped"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Total B grade parchment shipped to store in the past week"))
    grade_c_shipped = models.DecimalField(verbose_name=_("Grade C Shipped"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Total C grade parchment shipped to store in the past week"))

    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"),
                                    help_text=_("Whether this row is active"))

    objects = ActiveManager()
    all = models.Manager()

    EXPORT_FIELDS = (dict(label=_("Wetmill"), field='wetmill'),
                     dict(label=_("Week Starting"), field='start_of_week', weight=True),
                     dict(label=_("Grade A Stored"), field='grade_a_stored', weight=True),
                     dict(label=_("Grade B Stored"), field='grade_b_stored', weight=True),
                     dict(label=_("Grade C Stored"), field='grade_c_stored', weight=True),
                     dict(label=_("Grade A Shipped"), field='grade_a_shipped', weight=True),
                     dict(label=_("Grade B Shipped"), field='grade_b_shipped', weight=True),
                     dict(label=_("Grade C Shipped"), field='grade_c_shipped', weight=True))

    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - sitoki" % (self.wetmill.name,)

    def get_data(self): # pragma: no cover
        data = []

        calculated = self.get_calculated_values()
        
        data.append(dict(value=self.start_of_week, display_class='date'))
        data.append(dict(value=self.grade_a_stored, total=True))
        data.append(dict(value=self.grade_b_stored, total=True))
        data.append(dict(value=self.grade_c_stored, total=True))
        data.append(dict(value=self.grade_a_shipped, total=True))
        data.append(dict(value=self.grade_b_shipped, total=True))
        data.append(dict(value=self.grade_c_shipped, total=True))

        data.append(dict(value=calculated['total_stored'], display_class='calculated', total=True))
        data.append(dict(value=calculated['total_shipped'], display_class='calculated', total=True))
        data.append(dict(value=calculated['in_store'], display_class='calculated'))

        if self.submission:
            data.append(dict(value=self.submission.created, display_class='date'))

        return data

    def get_labels(self): # pragma: no cover
        return [ "Start of Week",
                 "Grade A Stored", "Grade B Stored", "Grade C Stored", "Grade A Shipped", "Grade B Shipped", "Grade C Shipped",
                 "Total Stored", "Total Shipped", "In Store", "Submitted" ]

    def get_calculated_values(self):
        calculated = dict()

        calculated['total_stored'] = comma_formatted(self.grade_a_stored + self.grade_b_stored + self.grade_c_stored, False)
        calculated['total_shipped'] = comma_formatted(self.grade_a_shipped + self.grade_b_shipped + self.grade_c_shipped, False)

        totals = SitokiSubmission.objects.filter(wetmill=self.wetmill, season=self.season, start_of_week__lte=self.start_of_week, created__lte=self.created).aggregate(
            Sum('grade_a_stored'), Sum('grade_b_stored'), Sum('grade_c_stored'), 
            Sum('grade_a_shipped'), Sum('grade_b_shipped'), Sum('grade_c_shipped'))
        
        stored = getd(totals, 'grade_a_stored__sum') + getd(totals, 'grade_b_stored__sum') + getd(totals, 'grade_c_stored__sum') - getd(totals, 'grade_a_shipped__sum') - getd(totals, 'grade_b_shipped__sum') - getd(totals, 'grade_c_shipped__sum')

        if not self.active:
            stored += self.grade_a_stored + self.grade_b_stored + self.grade_c_stored - self.grade_a_shipped - self.grade_b_shipped - self.grade_c_shipped

        calculated['in_store'] = comma_formatted(stored, False)


        calculated['week_start'] = self.start_of_week.strftime("%d.%m.%y")
        calculated['week_end'] = (self.start_of_week + timedelta(days=6)).strftime("%d.%m.%y")

        calculated['wetmill'] = self.wetmill

        return calculated

    def confirm(self):
        """
        Called when this message is confirmed
        """
        template_vars = self.get_calculated_values()
        template_vars['wetmill'] = self.wetmill

        SitokiSubmission.objects.filter(wetmill=self.wetmill, start_of_week=self.start_of_week).exclude(id=self.pk).update(active=False, is_active=False)

        # send off any cc's
        send_wetmill_ccs(self.submission.connection, self.submission.xform, self.wetmill, template_vars)            

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating an SitokiSubmission
        """
        print 'Any output here?'
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'sitoki' and not submission.has_errors:
            grade_a_stored = from_country_weight(submission.eav.sitoki_grade_a_stored, country)
            grade_b_stored = from_country_weight(submission.eav.sitoki_grade_b_stored, country)
            grade_c_stored = from_country_weight(submission.eav.sitoki_grade_c_stored, country)
            grade_a_shipped = from_country_weight(submission.eav.sitoki_grade_a_shipped, country)
            grade_b_shipped = from_country_weight(submission.eav.sitoki_grade_b_shipped, country)
            grade_c_shipped = from_country_weight(submission.eav.sitoki_grade_c_shipped, country)


            wetmill = submission.eav.sitoki_accountant.wetmill

            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = wetmill
            
            # is a season open?
            season = get_season(country)
            if not season: # pragma: no cover
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, wetmill, ['2012']):
                return

            now = datetime.now(pytz.utc)
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            week_start = get_week_start_during(datetime_for_daylot(submission.eav.sitoki_date).date())

            # if this week isn't yet over, that is an error
            if week_start + timedelta(days=7) > datetime.now().date():
                submission.has_errors = True
                submission.response = Blurb.get(submission.xform, 'future_submission', dict(),
                                                "You cannot submit a stock submission for a week that is not yet complete, specify the starting date of the week for sitoki messages")
                return

                # create our Sitoki Submission, they start off as NOT active
            sub = SitokiSubmission.objects.create(submission=submission,
                                                     active=False,
                                                     start_of_week=week_start,
                                                     accountant=submission.eav.sitoki_accountant,
                                                     wetmill=wetmill,
                                                     season=season,
                                                     grade_a_stored=grade_a_stored,
                                                     grade_b_stored=grade_b_stored,
                                                     grade_c_stored=grade_c_stored,
                                                     grade_a_shipped=grade_a_shipped,
                                                     grade_b_shipped=grade_b_shipped,
                                                     grade_c_shipped=grade_c_shipped)


            # do our calculations and stuff them in our template
            submission.template_vars.update(sub.get_calculated_values())
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            approve_submission.apply_async(args=[sub, SitokiSubmission], countdown=ONE_HOUR)
            
# register as a listener for incoming forms
xform_received.connect(SitokiSubmission.create_submission, dispatch_uid='sitoki_submission')

class TwakinzeSubmission(SMSSubmission):
    accountant = models.ForeignKey(Accountant, null=True, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    report_day = models.DateField(null=False, verbose_name=_("Report Day"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))

    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"),
                                    help_text=_("Whether this row is active"))

    objects = ActiveManager()
    all = models.Manager()

    EXPORT_FIELDS = (dict(label=_("Wetmill"), field='wetmill'),
                     dict(label=_("Day"), field='report_day'))

    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - twakinze" % (self.wetmill.name,)

    def get_data(self): # pragma: no cover
        data = []
        data.append(dict(value=self.report_day, display_class='date'))
        data.append(dict(value="Wetmill Reported as Closed", colspan=6))
        data.append(dict(value=""))
        if self.submission:
            data.append(dict(value=self.submission.created, display_class='date'))
        return data

    def get_labels(self): # pragma: no cover
        return [ "Report Day", "Closed", "Submitted"]

    def confirm(self):
        """
        Called when this message is confirmed
        """
        template_vars = dict(wetmill=self.wetmill, report_day=self.report_day)

        # make any other ibitumbwe or twakinze submissions on this date inactive
        IbitumbweSubmission.objects.filter(wetmill=self.wetmill, report_day=self.report_day).update(active=False, is_active=False)
        TwakinzeSubmission.objects.filter(wetmill=self.wetmill, report_day=self.report_day).exclude(id=self.pk).update(active=False, is_active=False)

        # send off any cc's
        send_wetmill_ccs(self.submission.connection, self.submission.xform, self.wetmill, template_vars)            

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating an SitokiSubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the accountant form and it does not have errors
        if xform.get_primary_keyword() == 'twakinze' and not submission.has_errors:
            wetmill = submission.eav.twakinze_accountant.wetmill

            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = wetmill
            
            # is a season open?
            season = get_season(country)
            if not season: # pragma: no cover
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, wetmill, ['2012', 'LIT2']):
                return

            now = datetime.now(pytz.utc)
            submission.response = XForm.render_response(xform.response, submission.template_vars)
            day = datetime_for_daylot(submission.eav.twakinze_date).date()

            sub = TwakinzeSubmission.objects.create(submission=submission,
                                                    active=False,
                                                    report_day=day,
                                                    accountant=submission.eav.twakinze_accountant,
                                                    wetmill=wetmill,
                                                    season=season)

            # do our calculations and stuff them in our template
            submission.response = XForm.render_response(xform.response, submission.template_vars)
            approve_submission.apply_async(args=[sub, TwakinzeSubmission], countdown=ONE_HOUR)
            
# register as a listener for incoming forms
xform_received.connect(TwakinzeSubmission.create_submission, dispatch_uid='twakinze_submission')

class IgurishaSubmission(SMSSubmission):
    # This is the green sales report
    buyer = models.TextField(null=False, verbose_name=_("Buyer"))
    accountant = models.ForeignKey(Accountant, null=True, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    sales_date = models.DateField(null=False, verbose_name=_("Sales Date"))
    grade = models.TextField(verbose_name=_("Grade"),
                                         help_text=_("The grade"))
    volume = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Volume"))
    price = models.DecimalField(verbose_name=_("Price"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("The price"))
    currency = models.CharField(max_length=1, help_text="Currency symbol", verbose_name=_("Currency"))
    exchange_rate = models.DecimalField(verbose_name=_("Exchange rate"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("The exchange rate"))
    sale_type = models.CharField(max_length=3, help_text="Type of sale (FOT, FOB, L)", verbose_name=_("Sale Type"))

    
    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"),
                                    help_text=_("Whether this row is active"))

    objects = ActiveManager()
    all = models.Manager()

    EXPORT_FIELDS = (dict(label=_("Wetmill"), field='wetmill'),
                     dict(label=_("Sales Date"), field='sales_date'),
                     dict(label=_("Grade"), field='grade', weight=True),
                     dict(label=_("Volume"), field='volume', weight=True),
                     dict(label=_("Price"), field='price', weight=True),
                     dict(label=_("Currency"), field='currency', weight=True),
                     dict(label=_("Exchange Rate"), field='exchange_rate', weight=True),
                     dict(label=_("Sale Type"), field='sale_type', weight=True))

    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - igurisha" % (self.wetmill.name,)

    def get_data(self): # pragma: no cover
        data = []

        ''' calculated = self.get_calculated_values()
        
        data.append(dict(value=self.start_of_week, display_class='date'))
        data.append(dict(value=self.grade_a_stored, total=True))
        data.append(dict(value=self.grade_b_stored, total=True))
        data.append(dict(value=self.grade_c_stored, total=True))
        data.append(dict(value=self.grade_a_shipped, total=True))
        data.append(dict(value=self.grade_b_shipped, total=True))
        data.append(dict(value=self.grade_c_shipped, total=True))

        data.append(dict(value=calculated['total_stored'], display_class='calculated', total=True))
        data.append(dict(value=calculated['total_shipped'], display_class='calculated', total=True))
        data.append(dict(value=calculated['in_store'], display_class='calculated')) '''

        if self.submission:
            data.append(dict(value=self.submission.created, display_class='date'))

        return data

    def get_labels(self): # pragma: no cover
        return [ "Sales Date",
                 "Grade", "Volume", "Price", "Currency", "Exchange Rate", "Sale Type" ]

    def datetime_for_igurisha(self, datetime_value):
        return datetime_value.strftime("%d/%m/%Y")

    def get_calculated_values(self):
        calculated = dict()
 
        # Here's the response:
        # On {sales_date}, {wetmill.name} sold {volume} kg for {total_sale_amount} {curr} at {price} {curr}/kg.  If correct send "OK".  If not send a correct sms.

        calculated['sales_date'] = self.datetime_for_igurisha(self.sales_date)
        calculated['volume'] = comma_formatted(self.volume, True)
        calculated['total_sale_amount'] = comma_formatted(self.volume * self.price, True)
        calculated['price'] = comma_formatted(self.price, True)
        calculated['curr'] = self.currency
        calculated['wetmill'] = self.wetmill

        return calculated

    def confirm(self):
        """
        Called when this message is confirmed
        """
        template_vars = self.get_calculated_values()
        template_vars['wetmill'] = self.wetmill

        IgurishaSubmission.objects.filter(wetmill=self.wetmill, sales_date=self.sales_date).exclude(id=self.pk).update(active=False, is_active=False)

        # send off any cc's
        send_wetmill_ccs(self.submission.connection, self.submission.xform, self.wetmill, template_vars)            

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating an IgurishaSubmission or a SalesSubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the igurisha form and it does not have errors (The get_primary_keyword() 
        # function pulls the first word in the list of words we use to refer to the report.  
        # Even if there are other language keywords in the list, it's the first one that needs to get pulled in.)
        # There was a bug that was making this sms not work because the list of keywords saved in the database
        # for Igurisha started with "sales"  This meant that the submission wasn't getting saved because the 
        # system thought that it wasn't an igurisha message.  This is definitely something that needs to be fixed up.
        # The eav variables are prefixed with sales instead of igurisha for this very reason.  Igurisha = Sales

        if xform.get_primary_keyword() == 'sales' and not submission.has_errors: # The other keyword used for this is 'igurisha' This is what the system works with to pull the eav.
            grade = submission.eav.sales_grade

            wetmill = submission.eav.sales_accountant.wetmill

            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = wetmill
            
            # is a season open?
            season = get_season(country)
            if not season: # pragma: no cover
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, wetmill, ['2012']):
                return

            now = datetime.now(pytz.utc)
            submission.response = XForm.render_response(xform.response, submission.template_vars)

                # create our Igurisha Submission, they start off as NOT active
            sub = IgurishaSubmission.objects.create(submission=submission,
                                                     active=False,
                                                     sales_date=datetime.strptime(submission.eav.sales_sales_date, "%d.%m.%y"),
                                                     buyer=submission.eav.sales_buyer,
                                                     accountant=submission.eav.sales_accountant,
                                                     wetmill=wetmill,
                                                     season=season,
                                                     grade=grade,
                                                     volume=submission.eav.sales_volume,
                                                     price=submission.eav.sales_price,
                                                     currency=submission.eav.sales_curr,
                                                     exchange_rate=submission.eav.sales_exchange_rate,
                                                     sale_type=submission.eav.sales_type)


            # do our calculations and stuff them in our template
            submission.template_vars.update(sub.get_calculated_values())
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            approve_submission.apply_async(args=[sub, IgurishaSubmission], countdown=ONE_HOUR)
            
# register as a listener for incoming forms
xform_received.connect(IgurishaSubmission.create_submission, dispatch_uid='igurisha_submission')

class DepanseSubmission(SMSSubmission):
    # This is the green expenses report
    accountant = models.ForeignKey(Accountant, null=True, verbose_name=_("Accountant"))
    wetmill = models.ForeignKey(Wetmill, verbose_name=_("Wetmill"))
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    submission_date = models.DateField(null=False, verbose_name=_("Submission Date"))
    milling = models.DecimalField(verbose_name=_("Milling"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Milling expenses"))
    marketing = models.DecimalField(verbose_name=_("Marketing"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Marketing expenses"))
    export = models.DecimalField(verbose_name=_("Export"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Export expenses"))
    finance = models.DecimalField(verbose_name=_("Finance"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Finance expenses"))
    capex = models.DecimalField(verbose_name=_("Capex"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Capex expenses"))
    govt = models.DecimalField(verbose_name=_("Govt"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Govt expenses"))
    other = models.DecimalField(verbose_name=_("Other Expenses"),
                                          max_digits=16, decimal_places=2,
                                          help_text=_("Other Expenses"))
    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"),
                                    help_text=_("Whether this row is active"))

    objects = ActiveManager()
    all = models.Manager()

    EXPORT_FIELDS = (dict(label=_("Wetmill"), field='wetmill'),
                     dict(label=_("Submission Date"), field='submission_date'),
                     dict(label=_("Milling"), field='milling', weight=True),
                     dict(label=_("Marketing"), field='marketing', weight=True),
                     dict(label=_("Export"), field='export', weight=True),
                     dict(label=_("Finance"), field='finance', weight=True),
                     dict(label=_("Capex"), field='capex', weight=True),
                     dict(label=_("Govt"), field='govt', weight=True),
                     dict(label=_("Other"), field='other', weight=True))

    class Meta:
        # by default order by last created first
        ordering = ('-created',)

    def __unicode__(self): # pragma: no cover
        return "%s - depanse" % (self.wetmill.name,)

    def get_data(self): # pragma: no cover
        data = []

        ''' calculated = self.get_calculated_values()
        
        data.append(dict(value=self.start_of_week, display_class='date'))
        data.append(dict(value=self.grade_a_stored, total=True))
        data.append(dict(value=self.grade_b_stored, total=True))
        data.append(dict(value=self.grade_c_stored, total=True))
        data.append(dict(value=self.grade_a_shipped, total=True))
        data.append(dict(value=self.grade_b_shipped, total=True))
        data.append(dict(value=self.grade_c_shipped, total=True))

        data.append(dict(value=calculated['total_stored'], display_class='calculated', total=True))
        data.append(dict(value=calculated['total_shipped'], display_class='calculated', total=True))
        data.append(dict(value=calculated['in_store'], display_class='calculated')) '''

        if self.submission:
            data.append(dict(value=self.submission.created, display_class='date'))

        return data

    def get_labels(self): # pragma: no cover
        return [ "Submission Date",
                 "Milling", "Marketing", "Export", "Finance", "Capex", "Govt", "Other" ]

    def get_calculated_values(self):
        calculated = dict()

        # This is the response:
        # Wetmill {{wetmill.name}}: milling={{milling}} {{curr}}, marketing={{marketing}} {{curr}}, export={{export}} {{curr}}, finance={{finance}} {{curr}}, capex={{CAPEX}} {{curr}}, govt={{govt}} {{curr}}, other={{other}} {{curr}}. Total = {{tot}} {{curr}} Ok?
        
        
        calculated['wetmill'] = self.wetmill
        calculated['curr'] = self.wetmill.country.currency.currency_code
        calculated['milling'] = comma_formatted(self.milling, True)
        calculated['marketing'] = comma_formatted(self.marketing, True)
        calculated['export'] = comma_formatted(self.export, True)
        calculated['finance'] = comma_formatted(self.finance, True)
        calculated['capex'] = comma_formatted(self.capex, True)
        calculated['govt'] = comma_formatted(self.govt, True)
        calculated['other'] = comma_formatted(self.other, True)
        calculated['tot'] = comma_formatted(self.milling + self.marketing + self.export + self.finance + self.capex + self.govt + self.other, True)

        return calculated

    def confirm(self):
        """
        Called when this message is confirmed
        """
        template_vars = self.get_calculated_values()
        template_vars['wetmill'] = self.wetmill

        DepanseSubmission.objects.filter(wetmill=self.wetmill, submission_date=self.submission_date).exclude(id=self.pk).update(active=False, is_active=False)

        # send off any cc's
        send_wetmill_ccs(self.submission.connection, self.submission.xform, self.wetmill, template_vars)            

    @staticmethod
    def create_submission(sender, **kwargs):
        """
        Our XForms Signal hook for creating an DepanseSubmission
        """
        xform = kwargs['xform']
        submission = kwargs['submission']
        country = get_country_for_backend(submission.connection.backend.name)
        
        # if this is the depanse form and it does not have errors
        if xform.get_primary_keyword() == 'expenses' and not submission.has_errors: #The other keyword is 'depanse'.  Read the description in the Igurisha submission for more details.

            wetmill = submission.eav.expenses_accountant.wetmill

            # stuff our wetmill in the response
            submission.template_vars['wetmill'] = wetmill
            
            # is a season open?
            season = get_season(country)
            if not season: # pragma: no cover
                submission.response = "No open season, please contact CSP."
                return

            # check whether this is the right wetmill type
            if check_wetmill_type(submission, wetmill, ['2012']):
                return

            now = datetime.now(pytz.utc)
            submission.response = XForm.render_response(xform.response, submission.template_vars)

                # create our Depanse/Expenses Submission, they start off as NOT active
            sub = DepanseSubmission.objects.create(submission=submission,
                                                     active=False,
                                                     submission_date=datetime.strptime(submission.eav.expenses_date, "%d.%m.%y"),
                                                     accountant=submission.eav.expenses_accountant,
                                                     wetmill=wetmill,
                                                     season=season,
                                                     milling=submission.eav.expenses_milling,
                                                     marketing=submission.eav.expenses_marketing,
                                                     export=submission.eav.expenses_export,
                                                     finance=submission.eav.expenses_finance,
                                                     capex=submission.eav.expenses_capex,
                                                     govt=submission.eav.expenses_govt,
                                                     other=submission.eav.expenses_other)


            # do our calculations and stuff them in our template
            submission.template_vars.update(sub.get_calculated_values())
            submission.response = XForm.render_response(xform.response, submission.template_vars)

            approve_submission.apply_async(args=[sub, DepanseSubmission], countdown=ONE_HOUR)
            
# register as a listener for incoming forms
xform_received.connect(DepanseSubmission.create_submission, dispatch_uid='depanse_submission')


"""
Rounds a decimal to two decimal places.
"""
def roundd(value, places=".01"):
    if value is None: # pragma: no cover
        return None
    else:
        return value.quantize(Decimal(places))

def lookup_concrete_submission(sms_submission): # pragma: no cover
    submission = AmafarangaSubmission.objects.filter(pk=sms_submission.pk)
    if submission:
        return submission[0]

    submission = IbitumbweSubmission.objects.filter(pk=sms_submission.pk)
    if submission:
        return submission[0]

    submission = SitokiSubmission.objects.filter(pk=sms_submission.pk)
    if submission:
        return submission[0]

    submission = TwakinzeSubmission.objects.filter(pk=sms_submission.pk)
    if submission:
        return submission[0]

    submission = IgurishaSubmission.objects.filter(pk=sms_submission.pk)
    if submission:
        return submission[0]

    submission = DepanseSubmission.objects.filter(pk=sms_submission.pk)
    if submission:
        return submission[0]

    return None

def ok(sender, **kwargs):
    """
    Commits a message in the 2012 SMS system
    """
    xform = kwargs['xform']
    submission = kwargs['submission']
    country = get_country_for_backend(submission.connection.backend.name)

    if xform.get_primary_keyword() == 'ok' and not submission.has_errors:
        wetmill = submission.eav.ok_accountant.wetmill

        # stuff our wetmill in the response
        submission.template_vars['wetmill'] = wetmill
            
        # is a season open?
        season = get_season(country)
        if not season: # pragma: no cover
            submission.response = "No open season, please contact CSP."
            return

        # check whether this is the right wetmill type
        if check_wetmill_type(submission, wetmill, ['2012', 'LIT2']): # pragma: no cover
            return

        # look up the last message sent by this connection in the last day
        cutoff = datetime.now() - timedelta(days=1)
        last_submission = XFormSubmission.objects.filter(created__gte=cutoff,
          connection=submission.connection).order_by('-created', '-pk').exclude(id=submission.id).exclude(xform__keyword__startswith='undo')

        confirm_message = None

        # if we found a submission, see if that submission was a real SMS submission
        if last_submission:
            last_submission = last_submission[0]

            # try to find a submission that matches this message
            subs = SMSSubmission.all.filter(submission=last_submission).order_by('-created', '-pk')
            if subs:
                confirm_message = subs[0]

        # if we found the submission, make it active
        if confirm_message:
            # mark the message as active
            confirm_message.active = True
            confirm_message.save()

            concrete = lookup_concrete_submission(confirm_message)
            if concrete:
                concrete.confirm()
                concrete.is_active = True
                concrete.save()

            # look up the real class for this submission
            submission.template_vars['msg'] = last_submission

        # we couldn't find a message to cancel, tell them so
        else:
            submission.has_errors = True
            submission.save()   
            submission.response = Blurb.get(xform, 'no_confirm', dict(),
                                            "No previous submission found to confirm.")

xform_received.connect(ok, dispatch_uid='ok')

def deactivate_daily_dupes(sender, instance, raw, using, **kwargs):
    # active instance, we need to make others inactive
    if instance.active:
        if sender == IgurishaSubmission or sender == DepanseSubmission:
            instance.report_day = instance.created #For Igurisha, since we're not using the report_day field.  We will use the day the report was created.  We will clean up the dupes on that date.
        
        filter = TwakinzeSubmission.objects.filter(active=True,
                                                   season=instance.season,
                                                   wetmill=instance.wetmill,
                                                   report_day=instance.report_day)

        if instance.pk and sender == TwakinzeSubmission:
            filter = filter.exclude(pk=instance.pk)

        filter.update(active=False, is_active=False)

        filter = IbitumbweSubmission.objects.filter(active=True,
                                                    season=instance.season,
                                                    wetmill=instance.wetmill,
                                                    report_day=instance.report_day)

        if instance.pk and sender == IbitumbweSubmission:
            filter = filter.exclude(pk=instance.pk)

        filter.update(active=False, is_active=False)

        if instance.pk and sender == DepanseSubmission:
        
            filter = DepanseSubmission.objects.filter(active=True,
                                                        season=instance.season,
                                                        wetmill=instance.wetmill,
                                                        submission_date=instance.submission_date,
                                                        milling=instance.milling,
                                                        marketing=instance.marketing,
                                                        export=instance.export,
                                                        finance=instance.finance,
                                                        capex=instance.capex,
                                                        govt=instance.govt,
                                                        other=instance.other)
            
            if instance.pk and sender == DepanseSubmission:
                filter = filter.exclude(pk=instance.pk)
            
            filter.update(active=False, is_active=False)

    instance.is_active = instance.active


def deactivate_weekly_dupes(sender, instance, raw, using, **kwargs):
    # this instance is active, we need to make any other instances inactive for the same season/wetmill/week
    if instance.active:
        filter = sender.objects.filter(active=True,
                                       season=instance.season,
                                       wetmill=instance.wetmill,
                                       start_of_week=instance.start_of_week)

        if instance.pk:
            filter = filter.exclude(pk=instance.pk)

        filter.update(active=False, is_active=False)

    instance.is_active = instance.active

pre_save.connect(deactivate_weekly_dupes, sender=SitokiSubmission, dispatch_uid="deactivate_sitoki_dupes")
pre_save.connect(deactivate_weekly_dupes, sender=AmafarangaSubmission, dispatch_uid="deactivate_amafaranga_dupes")
pre_save.connect(deactivate_daily_dupes, sender=IbitumbweSubmission, dispatch_uid="deactivate_ibitumbwe_dupes")
pre_save.connect(deactivate_daily_dupes, sender=TwakinzeSubmission, dispatch_uid="deactivate_twakinze_dupes")
pre_save.connect(deactivate_daily_dupes, sender=IgurishaSubmission, dispatch_uid="deactivate_igurisha_dupes")
pre_save.connect(deactivate_daily_dupes, sender=DepanseSubmission, dispatch_uid="deactivate_depanse_dupes")
