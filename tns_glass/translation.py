from modeltranslation.translator import translator, TranslationOptions

from grades.models import *
from standards.models import *
from expenses.models import *
from cashuses.models import *
from cashsources.models import *
from farmerpayments.models import *
from rapidsms_xforms.models import XForm, XFormFieldConstraint
from cc.models import MessageCC
from sms_reports.models import Report
from blurbs.models import Blurb
from help.models import HelpMessage
from django_quickblocks.models import QuickBlock

# this file defines all the different fields we want translatable.

class NameTranslationOptions(TranslationOptions):
    fields = ('name',)

translator.register(Standard, NameTranslationOptions)
translator.register(StandardCategory, NameTranslationOptions)
translator.register(Grade, NameTranslationOptions)
translator.register(Expense, NameTranslationOptions)
translator.register(CashUse, NameTranslationOptions)
translator.register(CashSource, NameTranslationOptions)
translator.register(FarmerPayment, NameTranslationOptions)

class QuickBlockTranslationOptions(TranslationOptions):
    fields = ('title', 'summary', 'content')

translator.register(QuickBlock, QuickBlockTranslationOptions)

class XFormTranslationOptions(TranslationOptions):
    fields = ('response',)

translator.register(XForm, XFormTranslationOptions)

class XFormFieldConstraintTranslationOptions(TranslationOptions):
    fields = ('message',)

translator.register(XFormFieldConstraint, XFormFieldConstraintTranslationOptions)

class MessageCCTranslationOptions(TranslationOptions):
    fields = ('message',)

translator.register(MessageCC, MessageCCTranslationOptions)

class ReportTranslationOptions(TranslationOptions):
    fields = ('message',)

translator.register(Report, ReportTranslationOptions)

class BlurbTranslationOptions(TranslationOptions):
    fields = ('message',)

translator.register(Blurb, BlurbTranslationOptions)

class HelpTranslationOptions(TranslationOptions):
    fields = ('message',)

translator.register(HelpMessage, HelpTranslationOptions)

