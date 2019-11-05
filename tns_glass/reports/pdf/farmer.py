from decimal import Decimal
from django.utils.translation import ugettext as _
from reports.pdf.currencyvalue import CurrencyValue as CV, CV_ZERO

class FarmerRow(object):

    def __init__(self, label, slug_token, row_for, value, is_total=False):
        self.label = label
        self.row_for = row_for
        self.value = value
        self.is_total = is_total
        self.slug_token = slug_token

    def slug(self):
        return 'farmer__%s__%s' % (self.slug_token, self.row_for)

class FarmerBox(object):

    def __init__(self, report, production, sales, expenses, cash, currency):
        self.report = report
        self.production = production
        self.sales = sales
        self.expenses = expenses
        self.cash = cash
        self.currency = currency

        self.exchange = self.report.season.exchange_rate
        
        self.total_cherry = self.production.cherry_total
        self.green_ratio = self.production.cherry_to_green_ratio

        self.build_rows()
        self.calculate_percentages()

    def times_cherry(self, per_weight_unit_cherry): # pragma: no cover
        if per_weight_unit_cherry is None:
            return None

        if self.total_cherry is None:
            return None

        return self.total_cherry * per_weight_unit_cherry

    def per_weight_unit_green(self, value):
        if value is None or not self.total_cherry:
            return None

        per_weight_unit_cherry = value / self.total_cherry
        if self.green_ratio is None: # pragma: no cover
            return None
        else:
            return per_weight_unit_cherry * self.green_ratio

    def build_total_row(self, rows, label, slug_token, row_for):
        total = CV_ZERO

        for row in rows:
            if row.value:
                total += row.value
                
        return FarmerRow(label, slug_token, row_for, total, True)

    def percent(self, numerator, denominator):
        if not numerator is None and isinstance(numerator, CV):
            numerator = numerator.as_local(self.exchange)

        if not denominator is None and isinstance(denominator, CV):
            denominator = denominator.as_local(self.exchange)

        if numerator is None or not denominator:
            return None

        else:
            return (numerator * Decimal("100") / denominator).quantize(Decimal("1"))

    def calculate_percentages(self):
        total_profit = self.expenses.total_profit
        retained_profit = self.cash.retained_profit

        self.farmer_percentage = None
        if not total_profit is None and not retained_profit is None:
            self.farmer_percentage = self.percent(total_profit - retained_profit , total_profit)

        total_revenue = self.sales.total_revenue.as_local(self.exchange)
        total_price = self.per_weight_unit_green(total_revenue)

        self.price_share = self.percent(self.price, total_price)
        self.member_price_share = self.percent(self.member_price, total_price)
        self.non_member_price_share = self.percent(self.non_member_price, total_price)

        if self.report.season.has_members:
            self.farmer_price = self.member_price
            self.farmer_share = self.member_price_share
        else:
            self.farmer_price = self.price
            self.farmer_share = self.price_share

    def get_rows(self):
        return self.rows

    def build_rows(self):
        self.rows = []

        # build our advance payment
        self.rows.append(FarmerRow(_("Advance Payment"), 'advance_payment', 'ALL', self.expenses.total_advance))

        for payment in self.report.farmer_payments_for_season():
            total = None
            entry = payment.entry
            row_for = None

            if payment.applies_to == 'ALL':
                row_for = 'ALL'
                if entry:
                    total = CV(self.times_cherry(entry.all_per_kilo))
                self.rows.append(FarmerRow(payment.name, 'fp__%d' % payment.id, row_for, total))

            if payment.applies_to == 'BOT' or payment.applies_to == 'MEM':
                row_for = 'MEM'
                if entry:
                    total = CV(self.times_cherry(entry.member_per_kilo))
                self.rows.append(FarmerRow(payment.name, 'fp__%d' % payment.id, row_for, total))

            if payment.applies_to == 'BOT' or payment.applies_to == 'NON':
                row_for = 'NON'
                if entry is None:
                    total = None
                else:
                    total = CV(self.times_cherry(entry.non_member_per_kilo))
                self.rows.append(FarmerRow(payment.name, 'fp__%d' % payment.id, row_for, total))

        # calculate our totals
        label = _("Total Farmer Payment")

        # no members for this season means just having a simple total
        if not self.report.season.has_members:
            self.rows.append(self.build_total_row(self.rows, label, 'total', 'ALL'))

            self.total_paid = self.rows[-1].value
            self.total_paid_members = None
            self.total_paid_non_members = None

            self.price = self.per_weight_unit_green(self.rows[-1].value)
            self.member_price = None
            self.non_member_price = None

        else:
            self.price = None

            self.rows.append(self.build_total_row([row for row in self.rows if row.row_for in ('ALL', 'MEM')], label, 'total', 'MEM'))
            self.member_price = self.per_weight_unit_green(self.rows[-1].value)
            self.total_paid_members = self.rows[-1].value
            self.total_paid = self.rows[-1].value

            self.rows.append(self.build_total_row([row for row in self.rows[:-1] if row.row_for in ('ALL', 'NON')], label, 'total', 'NON'))
            self.non_member_price = self.per_weight_unit_green(self.rows[-1].value)
            self.total_paid_non_members = self.rows[-1].value



    
