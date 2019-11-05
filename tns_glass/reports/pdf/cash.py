from decimal import Decimal
from reports.pdf.currencyvalue import CurrencyValue as CV, CV_ZERO

class UseRow(object):

    def __init__(self, cashuse, total):
        self.cashuse = cashuse
        self.name = cashuse.name
        self.total = total

    def slug(self):
        return 'cashuse__%d' % self.cashuse.id

class SourceRow(object):

    def __init__(self, cashsource, total):
        self.cashsource = cashsource
        self.name = cashsource.name
        self.total = total

    def slug(self):
        return 'cashsource__%d' % self.cashsource.id

class CashBox(object):

    def __init__(self, report, production, sales, expenses, currency):
        self.report = report
        self.production = production
        self.sales = sales
        self.expenses = expenses
        self.currency = currency
        self.exchange = report.season.exchange_rate
        
        self.total_cherry = self.production.cherry_total

        self.build_uses()
        self.build_sources()

        self.populate_calculated()

    def build_sources(self):
        self.sources = []
        for source in self.report.cash_sources_for_season():
            total = None
            
            if source.entry:
                total = CV(source.entry.value)

            self.sources.append(SourceRow(source, total))

    def build_uses(self):
        self.uses = []
        for cashuse in self.report.cash_uses_for_season():
            total = None

            if cashuse.entry:
                total = CV(cashuse.entry.value)

            self.uses.append(UseRow(cashuse, total))
            
    def get_uses(self):
        return self.uses

    def get_sources(self):
        return self.sources

    def set_calculated_source_value(self, calculated_from, value):
        # iterate our sources, setting the value
        for source in self.sources:
            if source.cashsource.calculated_from == calculated_from:
                source.total = value

    def set_calculated_use_value(self, calculated_from, value):
        # iterate our uses, setting the value
        for use in self.uses:
            if use.cashuse.calculated_from == calculated_from:
                use.total = value

    def populate_calculated(self):
        # first calculate all our totals
        self.working_cap_utilized = CV_ZERO
        categories = self.expenses.get_categories()
        if categories:
            self.working_cap_utilized += categories[0].value

        self.working_cap_received = CV_ZERO
        if self.report.working_capital:
            self.working_cap_received = CV(self.report.working_capital)

        self.working_cap_repaid = CV_ZERO
        if self.report.working_capital_repaid:
            self.working_cap_repaid = CV(self.report.working_capital_repaid)

        cash_due = self.expenses.total_revenue

        # subtract all our category totals
        for category in categories[1:]:
            cash_due -= category.value

        # and our forex loss
        cash_due -= self.expenses.total_forex_loss

        # and our working capital received
        cash_due -= self.working_cap_received
        cash_due += self.working_cap_repaid
        
        self.cash_due = cash_due

        self.unused_working_capital = self.working_cap_received - self.working_cap_utilized - self.working_cap_repaid

        # calculate retained profit
        self.retained_profit = self.expenses.total_profit
        for use in self.uses:
            if use.total:
                self.retained_profit -= use.total

        if self.retained_profit.as_local(self.exchange) < 0:
            self.retained_profit = CV(0)

        # then set them on our sources of cash if appropriate
        self.set_calculated_source_value('WCAP', self.unused_working_capital)
        self.set_calculated_source_value('CDUE', self.cash_due)

        self.set_calculated_use_value('PROF', self.retained_profit)

        
    
    
