from django.db import models
from smartmin.models import *
from wetmills.models import Wetmill
from seasons.models import Season
from grades.models import Grade
from expenses.models import Expense
from locales.models import Currency
from cashuses.models import CashUse
from cashsources.models import CashSource
from farmerpayments.models import FarmerPayment
from decimal import Decimal
from django.utils.translation import ugettext_lazy as _

class ReportFinalizeException(Exception):
    def __init__(self, fields):
        msg = 'Unable to finalize report due to missing field values. Please fill out these fields and try again: %s' % ", ".join(fields)
        super(ReportFinalizeException, self).__init__(msg)

class Report(SmartModel):
    season = models.ForeignKey(Season, related_name='reports', verbose_name=_("Season"),
                               help_text=_("The season this report is summarizing"))
    wetmill = models.ForeignKey(Wetmill, related_name='reports', verbose_name=_("Wetmill"),
                                help_text=_("The wetmill that this report is being prepared for"))

    working_capital = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name=_("Working Capital"),
                                          help_text=_("The working capital the wetmill was provided in the local currency"))
    working_capital_repaid = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name=_("Working Capital Repaid"),
                                                 help_text=_("The working capital that was repaid by the wetmill in the local currency"))
    miscellaneous_revenue = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name=_("Miscellaneous Revenue"),
                                                 help_text=_("Miscellaneous revenue the wetmill earned over the course of the season, in the local currency"))
    cherry_production_by_members = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name=_("Cherry Production by Members"),
                                                       help_text=_("The total cherry production in kilos by members"))
    farmers = models.IntegerField(null=True, blank=True, verbose_name=_("Farmers"),
                                  help_text=_("The number of farmers contributing to this wetmill over the course of this season"))
    capacity = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name=_("Capacity"),
                                   help_text=_("The total capacity of this wetmill in kilos of parchment for the season"))

    is_finalized = models.BooleanField(default=False, verbose_name=_("Is Finalized"),
                                    help_text=_("Whether this report's entries has been finalized"))

    #============ calculated values after finalization ===============#

    farmer_price = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Farmer Price"),
                                       help_text=_("Calculated total farmer price (for members if there are some, or for farmers if not) In the local currency, per kilo of green"))

    farmer_share = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Farmer Share"),
                                       help_text=_("Calculated farmer share (for members if there are some, or for farmers if not) In the local currency, per kilo of green"))

    production_cost = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Production Cost"),
                                          help_text=_("Calculated production cost per kilo of green (in local currency)"))

    cherry_to_green_ratio = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Cherry to Green Ratio"),
                                                help_text=_("Calculated cherry to green ratio"))

    working_capital_one_season_ago = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Working Capital Received for the last Season"),
                                                         help_text=_("Working capital received for the last season."))

    working_capital_two_seasons_ago = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Working Capital Received two seasons ago"),
                                                          help_text=_("Working capital received two seasons ago."))

    working_capital_repaid_pct_one_season_ago = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Percentage of working capital repaid last season"),
                                                                    help_text=_("Percentage of working capital repaid last season"))

    working_capital_repaid_pct_two_seasons_ago = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Percentage of working capital repaid two seasons ago"),
                                                                     help_text=_("Percentage of working capital repaid two seasons ago"))

    total_sale_one_season_ago = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Total sale last season"),
                                                    help_text=_("Total sale last season"))

    total_sale_two_seasons_ago = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Total sale two seasons ago"),
                                                     help_text=_("Total sale two seasons ago"))

    total_profitability_one_season_ago = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Total profitability last season"),
                                                             help_text=_("Total profitability last season"))

    total_profitability_two_seasons_ago = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True, verbose_name=_("Total profitability two seasons ago"),
                                                              help_text=_("Total profitability two seasons ago"))

    def farmer_price_usd(self):
        exchange = self.season.exchange_rate
        if self.farmer_price and exchange:
            return self.farmer_price / exchange
        else:
            return None

    def production_cost_usd(self):
        exchange = self.season.exchange_rate
        if self.production_cost and exchange:
            return self.production_cost / exchange
        else:
            return None

    @classmethod
    def get_for_wetmill_season(cls, wetmill, season, user=None):
        # try to look up an existing report
        existing = Report.objects.filter(wetmill=wetmill, season=season)
        if existing:
            return existing[0]
        else:
            if user:
                return Report.objects.create(wetmill=wetmill, season=season, created_by=user, modified_by=user)
            else: # pragma: no cover
                return None

    @classmethod
    def load_for_wetmill_season(cls, wetmill, season):
        report_entry = Report.objects.filter(wetmill=wetmill, season=season)
        if report_entry:
            return report_entry[0]
        else:
            return None

    def entries_for_season_expenses(self):
        """
        Returns a list containing a list for each top level category of expense for this report season.
        """
        season_expenses = []

        for expense in self.season.get_expense_tree():
            expense_entry = dict(expense=expense, value=None, exchange_rate=None)
            report_entry = self.expenses.filter(expense=expense)
            if report_entry:
                expense_entry['value'] = report_entry[0].value
                expense_entry['exchange_rate'] = report_entry[0].exchange_rate

            season_expenses.append(expense_entry)

        return season_expenses

    def cash_uses_for_season(self):
        """
        Returns a list containing all the configured cashuses for our season, each with an additional 'entry'
        attribute is set to the entry for this report
        """
        cashuses = self.season.get_cash_uses()
        for cashuse in cashuses:
            entry = self.cash_uses.filter(cash_use=cashuse)
            if entry:
                cashuse.entry = entry[0]
            else:
                cashuse.entry = None

        return cashuses


    def cash_sources_for_season(self):
        """
        Returns a list containing all the configured cash sources for our season, each with an additional 'entry'
        attribute is set to the entry for this report
        """
        cashsources = self.season.get_cash_sources()
        for cashsource in cashsources:
            entry = self.cash_sources.filter(cash_source=cashsource)
            if entry:
                cashsource.entry = entry[0]
            else:
                cashsource.entry = None

        return cashsources

    def farmer_payments_for_season(self):
        """
        Returns a list containing all the configured farmer payments for our season, each with an additional 'entry'
        attribute is set to the entry for this report
        """
        payments = self.season.get_farmer_payments()
        for payment in payments:
            entry = self.farmer_payments.filter(farmer_payment=payment)
            if entry:
                payment.entry = entry[0]
            else:
                payment.entry = None

        return payments

    def production_for_season_grades(self, kind=None):
        """
        Returns a list of dicts which contain the grade and volume set for all grades configured
        for this report's season
        """
        season_production = []

        if kind:
            season_grades = self.season.get_grade_tree(kind=kind)
        else:
            season_grades = self.season.get_grade_tree()

        for grade in season_grades:
            grade_production = dict(grade=grade, volume=None)
            report_production = self.production.filter(grade=grade)
            if report_production:
                grade_production['volume'] = report_production[0].volume

            season_production.append(grade_production)

        return season_production

    def production_for_kind(self, kind):
        """
        Returns the total production for the passed in category.  If there is no production set for
        the given category, then returns None
        """
        kind_production = self.production.filter(grade__kind=kind)
        if not kind_production:
            return None

        total_volume = Decimal("0")
        for production in kind_production:
            total_volume += production.volume

        return total_volume

    def cherry_production_by_non_members(self):
        """
        Calculates our cherry production by non-members.  We only have a value for this if both Cherry
        production has been set and the cherry production by members has been set
        """
        if self.cherry_production_by_members is None:
            return None

        cherry_production = self.production_for_kind('CHE')
        if cherry_production is None:
            return None

        return cherry_production - self.cherry_production_by_members

    def calculate_metrics(self):
        """
        Calculates the metrics for this report.  To do this the report must be finalized or raise
        an exception.
        """
        self.build_report_boxes(self.season.country.currency)
        exchange = self.season.exchange_rate

        self.farmer_price = self.farmer_box.farmer_price.as_local(exchange)
        self.farmer_share = self.farmer_box.farmer_share
        self.production_cost = self.expenses_box.production_cost.as_local(exchange)
        self.cherry_to_green_ratio = self.production_box.cherry_to_green_ratio

    def build_report_boxes(self, currency):
        from reports.pdf.production import ProductionBox
        from reports.pdf.sales import SalesBox
        from reports.pdf.expenses import ExpenseBox
        from reports.pdf.farmer import FarmerBox
        from reports.pdf.cash import CashBox
        from reports.models import Report

        self.production_box = ProductionBox(self)
        self.sales_box = SalesBox(self, currency)
        self.expenses_box = ExpenseBox(self, self.production_box, self.sales_box, currency)
        self.cash_box = CashBox(self, self.production_box, self.sales_box, self.expenses_box, currency)
        self.farmer_box = FarmerBox(self, self.production_box, self.sales_box, self.expenses_box, self.cash_box, currency)

    def finalize(self):
        empty_fields = []

        if self.farmers is None:
            empty_fields.append('Number of farmers')

        if self.capacity is None:
            empty_fields.append("Capacity")

        for cashsource in self.cash_sources_for_season():
            if cashsource.entry is None and cashsource.calculated_from == 'NONE':
                empty_fields.append(cashsource.name)

        for cashuse in self.cash_uses_for_season():
            if cashuse.entry is None and cashuse.calculated_from == 'NONE':
                empty_fields.append(cashuse.name)

        for payment in self.farmer_payments_for_season():
            missing = True
            entry = payment.entry

            if not entry is None:
                if payment.applies_to == 'MEM':
                    missing = entry.member_per_kilo is None
                elif payment.applies_to == 'BOT':
                    missing = entry.member_per_kilo is None or entry.non_member_per_kilo is None
                elif payment.applies_to == 'NON':
                    missing = entry.non_member_per_kilo is None
                else:
                    missing = entry.all_per_kilo is None

            if missing:
                empty_fields.append(payment.name)

        for entry in self.entries_for_season_expenses():
            expense = entry['expense']
            if not expense.is_parent and expense.calculated_from == 'NONE' and entry['value'] is None:
                empty_fields.append(entry['expense'].name)

        for entry in self.production_for_season_grades():
            if not entry['grade'].is_parent and entry['volume'] is None:
                empty_fields.append(entry['grade'].name)

        if len(self.sales.all()) < 1:
            empty_fields.append("Add at least one sale")

        # more than one missing value, raise an exception
        if len(empty_fields) > 0:
            raise ReportFinalizeException(empty_fields)

        # ok, all good, mark ourselves as finalized and calculate our metrics
        self.is_finalized = True
        self.calculate_metrics()

    def __unicode__(self):
        return "%s %s" % (self.wetmill.name, self.season.name)

    class Meta:
        unique_together = ('season', 'wetmill')

class ReportAmendments(SmartModel):
    report = models.ForeignKey(Report, related_name='amendments', verbose_name=_("Report"))
    description = models.TextField(verbose_name=_("Description"))

class Production(SmartModel):
    report = models.ForeignKey(Report, related_name='production', verbose_name=_("Report"))
    grade = models.ForeignKey(Grade, verbose_name=_("Grade"),
                              help_text=_("The coffee grade that was produced"))
    volume = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Volume"),
                                 help_text=_("The volume of coffee that was produced"))

    class Meta:
        unique_together = ('report', 'grade')
        ordering = ('grade__order', 'grade__name')

class CashUseEntry(SmartModel):
    report = models.ForeignKey(Report, related_name='cash_uses', verbose_name=_("Report"))
    cash_use = models.ForeignKey(CashUse, verbose_name=_("Cash Use"),
                                 help_text=_("The use of cash that we are recording an entry for"))
    value = models.DecimalField(max_digits=16, decimal_places=2, null=True, verbose_name=_("Value"),
                                help_text=_("The value of the cash use, in the local currency"))

class CashSourceEntry(SmartModel):
    report = models.ForeignKey(Report, related_name='cash_sources', verbose_name=_("Report"))
    cash_source = models.ForeignKey(CashSource, verbose_name=_("Cash Source"),
                                    help_text=_("The source of cash that we are recording an entry for"))
    value = models.DecimalField(max_digits=16, decimal_places=2, null=True, verbose_name=_("Value"),
                                help_text=_("The value of the cash source, in the local currency"))

class FarmerPaymentEntry(SmartModel):
    report = models.ForeignKey(Report, related_name='farmer_payments', verbose_name=_("Report"))
    farmer_payment = models.ForeignKey(FarmerPayment, verbose_name=_("Farmer Payment"),
                                       help_text=_("The farmer payment that we are recording an entry for"))
    all_per_kilo = models.DecimalField(max_digits=16, decimal_places=2, null=True, verbose_name=_("All per Kilo"),
                                       help_text=_("The amount per kilo of cherry given to farmers, in the local currency"))
    member_per_kilo = models.DecimalField(max_digits=16, decimal_places=2, null=True, verbose_name=_("Member per Kilo"),
                                          help_text=_("The amount per kilo of cherry given to members, in the local currency"))
    non_member_per_kilo = models.DecimalField(max_digits=16, decimal_places=2, null=True, verbose_name=_("Non Member per Kilo"),
                                              help_text=_("The amount per kilo of cherry given to non-members, in the local currency"))

    class Meta:
        unique_together = ('report', 'farmer_payment')
        ordering = ('farmer_payment__order', 'farmer_payment__name')

class ExpenseEntry(SmartModel):
    report = models.ForeignKey(Report, related_name='expenses', verbose_name=_("Report"))
    expense = models.ForeignKey(Expense, verbose_name=_("Expense"),
                                help_text=_("The expense that we are recording the value for"))
    value = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Value"),
                                help_text=_("The value of the expense for this wetmill and season"))
    exchange_rate = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name=_("Exchange Rate"),
                                        help_text=_("For expenses in dollars, the exchange rate at the time of the expense"))

    def __unicode__(self):
        return '%s - %s (%s)' % (self.expense.name, self.value, self.exchange_rate)

    class Meta:
        unique_together = ('report', 'expense')
        ordering = ('expense__name',)

class Sale(SmartModel):
    TYPE_CHOICES = (('FOT', _("FOT - Free On Truck")),
                    ('FOB', _("FOB - Free On Board")),
                    ('LOC', _("Local Sale")))

    NO_LOCAL_TYPE_CHOICES = (('FOT', _("FOT - Free on Truck")),
                             ('FOB', _("FOB - Free on Board")))

    LOCAL_TYPE_CHOICES = TYPE_CHOICES

    report = models.ForeignKey(Report, related_name='sales', verbose_name=_("Report"))

    date = models.DateField(verbose_name=_("Date"), help_text=_("The date this sale was made"))
    buyer = models.CharField(max_length=64, verbose_name=_("Buyer"),
                             help_text=_("The name of the buyer in this sale"))
    currency = models.ForeignKey(Currency, verbose_name=_("Currency"),
                                 help_text=_("The currency used to pay for this sale"))
    price = models.DecimalField(max_digits=16, decimal_places=4, verbose_name=_("Price"),
                                help_text=_("The price paid per kilo"))
    exchange_rate = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name=_("Exchange Rate"),
                                        help_text=_("The exchange rate if the sale was made in US Dollars"))
    sale_type = models.CharField(max_length=3, choices=TYPE_CHOICES, verbose_name=_("Sale Type"),
                                 help_text=_("The type of sale, whether it was Free on Board, or Free on Truck"))
    adjustment = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name=_("Adjustment"),
                                     help_text=_("The adjustment price based on the sale type"))


    def total_volume(self):
        volume = Decimal("0")
        for component in self.components.all():
            volume += component.volume
        return volume

    def all_grades(self):
        grades = []
        for component in self.components.all():
            if not component.grade.name in grades:
                grades.append(component.grade.name)

        return ", ".join(grades)  

    def __unicode__(self):
        return 'Sale to %s' % self.buyer

    class Meta:
        ordering = ('date',)

class SaleComponent(SmartModel):
    sale = models.ForeignKey(Sale, related_name='components', verbose_name=_("Sale"))
    grade = models.ForeignKey(Grade, related_name='sale_components', verbose_name=_("Grade"))
    volume = models.DecimalField(max_digits=16, decimal_places=2, verbose_name=_("Volume"))

    class Meta:
        ordering = ('grade__name',)


