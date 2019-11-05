from decimal import Decimal, ROUND_HALF_UP
from reports.pdf.currencyvalue import CurrencyValue as CV, CV_ZERO

class ExpenseRow(object):

    def __init__(self, expense, value=None, children=None):
        self.expense = expense
        self.name = expense.name

        if children:
            self.children = children
            self.value = CV_ZERO
            self.advance_value = CV_ZERO
            for child in self.children:
                self.value += child.value
                self.advance_value += child.advance_value

        else:
            self.value = value
            self.children = []

            if self.expense.is_advance:
                self.advance_value = self.value
            else:
                self.advance_value = None

    # returns any label for this expense or it's children.. Freight and Insurance being an example
    def get_calculated_legend(self):
        label = self.expense.get_calculated_legend()
        if label:
            return label
        else:
            for child in self.children:
                label = child.get_calculated_legend()
                if label:
                    return label

        return None

    def slug(self):
        return "expense__%d" % self.expense.id

    def non_advance_value(self):
        return self.value - self.advance_value

    def __repr__(self):
        return "%s - %s" % (self.name, self.value)

class ExpenseBox(object):

    def __init__(self, report, production_box, sales_box, currency):
        self.report = report
        self.production_box = production_box
        self.sales_box = sales_box
        self.currency = currency
        self.exchange = self.report.season.exchange_rate

        self.sales_revenue = sales_box.total_revenue
        self.total_revenue = sales_box.total_revenue
        self.misc_revenue = CV(None)

        # if we have misc revenue (TZ in some cases) then our total must take that into account
        if self.report.season.has_misc_revenue:
            self.misc_revenue = CV(self.report.miscellaneous_revenue)
            self.total_revenue += self.misc_revenue

        self.categories = self.build_category_rows()

        self.calculate_totals()

    def get_categories(self):
        return self.categories

    def calculate_totals(self):
        self.total = CV(Decimal("0"))
        self.total_advance = CV(Decimal("0"))
        self.total_expense = CV(Decimal("0"))

        # calculate our overall advance
        for category in self.categories:
            self.total += category.value
            self.total_advance += category.advance_value

        # total forex loss
        self.total_forex_loss = self.total_revenue.forex_loss(self.exchange) - self.total.forex_loss(self.exchange)

        # total profit
        self.total_profit = self.total_revenue - self.total - self.total_forex_loss

        # total expenses per kilo green
        total_expense = self.total - self.total_advance
        if self.production_box.green_total:
            self.production_cost = total_expense / self.production_box.green_total
        else:
            self.production_cost = CV(Decimal("0"))

    def build_row(self, expense, value, children=None):
        # overload any calculated values here
        if expense.calculated_from == 'FREIGHT':
            value = self.sales_box.total_freight

        if children:
            return ExpenseRow(expense, children=children)
        else:
            return ExpenseRow(expense, value=value)

    def build_expense_row(self, entries, index):
        row = entries[index]
        children = []

        for i in range(index+1, len(entries)):
            entry = entries[i]

            if entry['expense'].depth <= 1:
                break

            children.append(self.build_row(entry['expense'], CV(entry['value'], entry['exchange_rate'])))

        return self.build_row(row['expense'], CV(row['value'], row['exchange_rate']), children)

    def build_category_row(self, entries, index):
        category = entries[index]
        children = []

        for i in range(index+1, len(entries)):
            entry = entries[i]
            
            # new category?  all done
            if entry['expense'].depth == 0:
                break

            # depth 1?  roll it up
            if entry['expense'].depth == 1:
                row = self.build_expense_row(entries, i)
                children.append(row)

        return self.build_row(category['expense'], CV(category['value'], category['exchange_rate']), children)

    def build_category_rows(self):
        categories = []

        entries = self.report.entries_for_season_expenses()
        for (index, entry) in enumerate(entries):
            # if this is a category, build our rollup for it
            if entry['expense'].depth == 0:
                categories.append(self.build_category_row(entries, index))

        return categories

