from django.db import models
from smartmin.models import SmartModel
from locales.models import *
from expenses.models import *
from grades.models import *
from standards.models import *
from cashuses.models import *
from cashsources.models import *
from farmerpayments.models import *
from django.utils.translation import ugettext_lazy as _
import requests
from lxml.html import fromstring
from lxml.cssselect import CSSSelector
import re

class Season(SmartModel):
    name = models.CharField(max_length=16, verbose_name=_("Name"),
                            help_text=_("The name of the season, typically just the year"))
    country = models.ForeignKey(Country, verbose_name=_("country"),
                                help_text=_("The country this season took place in"))
    exchange_rate = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Exchange Rate"),
                                        help_text=_("The exchange rate to US dollars to use for this season"))
    default_adjustment = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Default Adjustment"),
                                             help_text=_("The default FOT/FOB adjustment to use for this season, in US dollars"))
    has_local_sales = models.BooleanField(default=False, verbose_name=_("Has Local Sales"),
                                          help_text=_("Whether local sales are supported for this season"))
    has_members = models.BooleanField(default=False, verbose_name=_("Has Member"),
                                      help_text=_("Whether the wetmills in this season have members.  Tanzania for example does not"))
    has_misc_revenue = models.BooleanField(default=False,
                                           verbose_name=_("Has miscellaneous revenue"),
                                           help_text=_("Whether reports should include a field for miscellaneous revenue. Tanzania for example does."))

    farmer_income_baseline = models.DecimalField(max_digits=16, decimal_places=2,
                                                 verbose_name=_("Income Baseline"),
                                                 help_text=_("The baseline farmer income for this country in season, in the local currency, per kilo of green"))
    fob_price_baseline = models.DecimalField(max_digits=16, decimal_places=2,
                                             verbose_name=_("FOB Baseline"),
                                             help_text=_("The baseline FOB export price for coffee, in the local currency, per kilo of green"))

    expenses = models.ManyToManyField(Expense, through='SeasonExpense', verbose_name=_("Expenses"),
                                      help_text=_("The expenses that are active for this season"))
    grades = models.ManyToManyField(Grade, through='SeasonGrade', verbose_name=("Grades"),
                                    help_text=_("The grades that are active for this season"))
    standards = models.ManyToManyField(Standard, verbose_name=_("standards"),
                                       help_text=_("The standards that are active for this season"))
    cash_sources = models.ManyToManyField(CashSource, verbose_name=_("Cash Sources"),
                                          help_text=_("The sources of cash that are active for this season"))
    cash_uses = models.ManyToManyField(CashUse, verbose_name=_("Cash Uses"),
                                       help_text=_("The uses of cash that are active for this season"))
    is_finalized = models.BooleanField(default=False, verbose_name=_("Is Finalized"),
                                       help_text=_("Whether this season has been finalized at least once"))

    farmer_payment_left = models.DecimalField(max_digits=16, decimal_places=4, default=0, verbose_name=_("Farmer Payment Left"),
                                             help_text=_("The left value for the farmer payment gauge, in the local currency per kilo of cherry"))
    farmer_payment_right = models.DecimalField(max_digits=16, decimal_places=4, default=100, verbose_name=_("Farmer Payment Right"),
                                             help_text=_("The right value for the farmer payment gauge, in the local currency per kilo of cherry"))

    cherry_ratio_left = models.DecimalField(max_digits=16, decimal_places=4, default=12, verbose_name=_("Cherry Ratio Left"),
                                           help_text=_("The left value for the cherry ratio gauge"))
    cherry_ratio_right = models.DecimalField(max_digits=16, decimal_places=4, default=5, verbose_name=_("Cherry Ratio Right"),
                                           help_text=_("The right value for the cherry ratio gauge"))

    total_costs_left = models.DecimalField(max_digits=16, decimal_places=4, default=0, verbose_name=_("Total Costs Left"),
                                          help_text=_("The left value for the total cost gauge, in the local currency per kilo of green"))
    total_costs_right = models.DecimalField(max_digits=16, decimal_places=4, default=100, verbose_name=_("Total Costs Right"),
                                          help_text=_("The right value for the total cost gauage, in the local currency per kilo of green"))

    sale_price_left = models.DecimalField(max_digits=16, decimal_places=4, default=0, verbose_name=_("Sale Price Left"),
                                         help_text=_("The left value for the sale price gauge, in the local currency per kilo of green (FOT)"))
    sale_price_right = models.DecimalField(max_digits=16, decimal_places=4, default=10, verbose_name=_("Sale Price Right"),
                                         help_text=_("The right value for the sale price gauge, in the local currency per kilo of green (FOT)"))

    @classmethod
    def get_last_country_season(cls, country, exclude_season=None):
        previous = Season.objects.filter(country=country)
        if exclude_season:
            previous = previous.exclude(pk=exclude_season.pk)

        if not previous:
            return None
        else:
            return previous[0]

    # Get previous two seasons for the currently loaded season.
    # Used to calculate trends.
    def get_previous_two_seasons(self):
        previous = Season.objects.filter(country=self.country).filter(created_on__lte=self.created_on).exclude(pk=self.pk).order_by('-created_on')

        if not previous:
            return None
        else:
            return previous[:2]

    def clone_from_last(self):
        previous = Season.get_last_country_season(self.country, self)

        # copy over our gauge fields as well
        clone_fields = ('exchange_rate', 'default_adjustment', 'has_local_sales', 'has_members', 'has_misc_revenue',
                        'farmer_income_baseline', 'fob_price_baseline',
                        'sale_price_left', 'sale_price_right', 'total_costs_left', 'total_costs_right',
                        'cherry_ratio_left', 'cherry_ratio_right', 'farmer_payment_left', 'farmer_payment_right')

        for field in clone_fields:
            setattr(self, field, getattr(previous, field, None))

    def clone_m2m_from_last(self):
        previous = Season.get_last_country_season(self.country, self)

        # copy our expenses
        for expense in previous.get_expense_tree():
            self.add_expense(expense, expense.collapse)

        # grades
        for grade in previous.get_grade_tree():
            self.add_grade(grade, grade.is_top_grade)

        # cash sources
        for cashsource in previous.get_cash_sources():
            self.add_cash_source(cashsource)

        # cash uses
        for cashuse in previous.get_cash_uses():
            self.add_cash_use(cashuse)

        # farmer payments
        for payment in previous.get_farmer_payments():
            self.add_farmer_payment(payment, payment.applies_to)

        # standards
        for standard in previous.get_standards():
            self.add_standard(standard)

    def clone_wetmill_assignments_from_last(self):
        previous = Season.get_last_country_season(self.country, self)

        # clone our wetmill->csp assignments
        from wetmills.models import WetmillCSPSeason
        for wetmill_csp in WetmillCSPSeason.objects.filter(season=previous):
            if not WetmillCSPSeason.objects.filter(season=self, wetmill=wetmill_csp.wetmill):
                WetmillCSPSeason.objects.create(season=self, wetmill=wetmill_csp.wetmill, csp=wetmill_csp.csp)

        # clone our accounting systems from last season
        from wetmills.models import WetmillSeasonAccountingSystem
        for wetmill_accounting in WetmillSeasonAccountingSystem.objects.filter(season=previous):
            if not WetmillSeasonAccountingSystem.objects.filter(season=self, wetmill=wetmill_accounting.wetmill):
                WetmillSeasonAccountingSystem.objects.create(season=self, wetmill=wetmill_accounting.wetmill,
                                                             accounting_system=wetmill_accounting.accounting_system)

    def get_grades(self):
        return SeasonGrade.objects.filter(season=self)

    def add_grade(self, grade, is_top=False):
        SeasonGrade.objects.filter(season=self, grade=grade).delete()
        return SeasonGrade.objects.create(season=self, grade=grade, is_top_grade=is_top)

    def get_standard_categories(self):
        standard_categories = set()
        for standard in self.standards.all():
            standard_categories.add(standard.category)

        return standard_categories

    def get_cash_uses(self):
        return self.cash_uses.all()

    def get_cash_sources(self):
        return self.cash_sources.all()

    def get_farmer_payments(self):
        season_payments = []
        for farmer_payment in SeasonFarmerPayment.objects.filter(season=self):
            payment = farmer_payment.farmer_payment
            payment.applies_to = farmer_payment.applies_to
            season_payments.append(payment)

        return season_payments

    def get_expenses(self):
        return SeasonExpense.objects.filter(season=self)

    def add_expense(self, expense, collapse=False):
        SeasonExpense.objects.filter(season=self, expense=expense).delete()
        return SeasonExpense.objects.create(season=self, expense=expense, collapse=collapse)

    def add_farmer_payment(self, payment, applies_to):
        SeasonFarmerPayment.objects.filter(season=self, farmer_payment=payment).delete()
        return SeasonFarmerPayment.objects.create(season=self, farmer_payment=payment, applies_to=applies_to)

    def add_cash_source(self, cashsource):
        self.cash_sources.remove(cashsource)
        self.cash_sources.add(cashsource)

    def add_cash_use(self, cashuse):
        self.cash_uses.remove(cashuse)
        self.cash_uses.add(cashuse)

    def add_standard(self, standard):
        self.standards.remove(standard)
        self.standards.add(standard)

    def get_standards(self, category=None):
        return self.standards.all() if category is None else self.standards.filter(category=category)

    def get_expense_tree(self):
        season_ids = [expense.id for expense in self.expenses.all()]
        season_expenses = []
        for top_expense in self.expenses.filter(parent=None):
            top_expense.depth = 0
            season_expenses.append(top_expense)
            season_expenses += top_expense.get_child_tree(id__in=season_ids)

        # now figure out for each expense whether it has children in the context of this season
        for i in range(len(season_expenses)):
            if i+1 < len(season_expenses) and season_expenses[i+1].depth > season_expenses[i].depth:
                season_expenses[i].is_parent = True
            else:
                season_expenses[i].is_parent = False

            # and set whether it should be collapsed
            season_expense = SeasonExpense.objects.get(season=self, expense=season_expenses[i])
            season_expenses[i].collapse = season_expense.collapse

        return season_expenses

    def get_grade_tree(self, **kwargs):
        season_ids = [grade.id for grade in self.grades.all()]
        season_grades = []
        for top_grade in self.grades.filter(parent=None, **kwargs):
            top_grade.depth = 0
            season_grades.append(top_grade)
            season_grades += top_grade.get_child_tree(id__in=season_ids)
            
        # figure out for each grade wheter it has children in the context of this season
        for i in range(len(season_grades)):
            if i+1 < len(season_grades) and season_grades[i+1].depth > season_grades[i].depth:
                season_grades[i].is_parent = True
            else:
                season_grades[i].is_parent = False

            # and set whether it is a top grade
            season_grade = SeasonGrade.objects.get(season=self, grade=season_grades[i])
            season_grades[i].is_top_grade = season_grade.is_top_grade
                
        return season_grades

    def has_unprocessed_grades(self):
        for grade in self.grades.all():
            if grade.is_not_processed:
                return True

        return False

    def __unicode__(self):
        return "%s %s" % (self.country.name, self.name)

    def update_exchange_rate(self):
        print 'Starting update exchange rate sequence...'
        if self.is_active:
            url = settings.EXCHANGE_RATE_INFO_URL

            url = url.replace("{{CURRENCY_CODE}}", self.country.currency.currency_code)

            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

            if r.status_code == 200:
                html = fromstring(r.text)
                sel = CSSSelector(settings.CURRENCY_PRICE_SELECTOR)

                matches = sel(html)
                if matches:
                    # remove anything that isn't numeric
                    rate = Decimal(re.sub('[^0-9\.]', '', matches[0].text))
                    self.exchange_rate = rate
                    self.save()
                    return rate

            return None

    class Meta:
        unique_together = ('country', 'name')
        ordering = ('country__name', '-name')


class SeasonExpense(models.Model):
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    expense = models.ForeignKey(Expense, verbose_name=_("Expense"))
    collapse = models.BooleanField(default=False, verbose_name=_("Collapse"),
                                   help_text=_("Whether to collapse this expense and hide its children when displayed in a report"))

    class Meta:
        ordering = ('expense__order',)
        unique_together = ('season', 'expense')

class SeasonGrade(models.Model):
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    grade = models.ForeignKey(Grade, verbose_name=_("Grade"))
    is_top_grade = models.BooleanField(default=False, verbose_name=_("Is Top Grade"),
                                       help_text=_("Whether this grade should be considered one of the 'top grades' for this season"))

    class Meta:
        ordering = ('grade__order',)
        unique_together = ('season', 'grade')

MODEL_PAYMENT_CHOICES = [('MEM', _("Coop members only")),
                         ('NON', _("Non members only")),
                         ('BOT', _("Both members and non-members")),
                         ('ALL', _("No membership, applies to all"))]

FORM_PAYMENT_CHOICES = [('XXX', _("Not used for this season"))]

HAS_MEMBERS_FORM_PAYMENT_CHOICES = FORM_PAYMENT_CHOICES + [('MEM', _("Coop members only")),
                                                           ('NON', _("Non members only")),
                                                           ('BOT', _("Both members and non-members"))]

NO_MEMBERS_FORM_PAYMENT_CHOICES = FORM_PAYMENT_CHOICES + [('ALL', _("No membership, applies to all"))]

class SeasonFarmerPayment(models.Model):
    season = models.ForeignKey(Season, related_name='farmer_payments', verbose_name=_("Season"))
    farmer_payment = models.ForeignKey(FarmerPayment, verbose_name=_("Farmer Payment"))
    applies_to = models.CharField(max_length=4, choices=MODEL_PAYMENT_CHOICES, verbose_name=_("Applies to"))

    class Meta:
        ordering = ('farmer_payment__order',)
        unique_together = ('season', 'farmer_payment')

