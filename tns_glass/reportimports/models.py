from django.db import models
from smartmin.models import SmartModel
from seasons.models import Season
from grades.models import Grade
from expenses.models import Expense
from cashuses.models import CashUse
from cashsources.models import CashSource
from farmerpayments.models import FarmerPayment
from wetmills.models import Wetmill
from reports.models import Report
from csps.models import CSP
from locales.models import Currency
from datetime import datetime
import csv
import re
from decimal import Decimal
from .tasks import import_reports
from django.utils.translation import ugettext_lazy as _

class ReportImport(SmartModel):
    season = models.ForeignKey(Season, verbose_name=_("Season"),
                               help_text=_("The season reports are being imported for"))
    csv_file = models.FileField(upload_to="report_imports", 
                                verbose_name=_("Import CSV File"),
                                help_text=_("The CSV file to import for this season, must be formatted according to the season template"))
    import_log = models.TextField(help_text=_("Any logging information about this import"), verbose_name=_("Import Log"))
    task_id = models.CharField(null=True, max_length=64, verbose_name=_("Task Id"))

    def __unicode__(self):
        return "CSV Import for %s %s" % (self.season.country.name, self.season.name)

    def start(self): # pragma: no cover
        result = import_reports.delay(self)
        self.task_id = result.task_id
        self.import_log = "Queuing file for import.\n"
        self.save()

    def get_status(self):
        status = 'PENDING'
        if self.task_id: # pragma: no cover
            result = import_reports.AsyncResult(self.task_id)
            status = result.state

        return status

    def log(self, message):
        self.import_log += "%s\n" % message
        self.modified_on = datetime.now()
        self.save()

    class Meta:
        ordering = ('-modified_on',)

def parse_label(label):
    match = re.match("^(.*?)\s+\[(.*?)\]\s*$", label, re.DOTALL | re.MULTILINE)
    if match:
        return (match.group(1), match.group(2))
    else:
        return (label, None)

def parse_buyer_grade(label):
    match = re.match("^(.*?)\s+\((.*)\)\s*$", label, re.DOTALL | re.MULTILINE)
    if match:
        return (match.group(1), match.group(2))
    else:
        raise Exception("Unable to parse buyer name and grade: '%s'  Format should be: 'Buyer (Grade)'" % label)

def get_grade(season, name):
    match = re.match("^\s*(.*?)\s+\(KG\)\s*", name, re.DOTALL | re.MULTILINE)
    if match:
        name = match.group(1)

    grade = Grade.from_full_name(name)

    if not grade:
        raise Exception("Unable to find grade with name '%s'" % name)

    # get the grade from our tree, this then includes depth and whether it has children
    # in the context of this season
    season_grades = season.get_grade_tree()
    for season_grade in season_grades:
        if season_grade.id == grade.id:
            return season_grade

    raise Exception("The grade '%s' is not a configured grade for the %s season" % (grade.name, season.name))

def get_wetmill(country, name):
    name = name.strip()
    try:
        return Wetmill.objects.get(country=country, name=name)
    except:
        raise Exception("Unable to find wetmill with name '%s'" % name)

def get_csp(name):
    name = name.strip()
    try:
        return CSP.objects.get(name=name)
    except:
        raise Exception("Unable to find a CSP with the name '%s'" % name)

def get_expense(season, parent, name):
    name = name.strip()
    try:
        expense = Expense.objects.get(parent=parent, name=name)
    except:
        if not parent:
            raise Exception("Unable to find expense with name '%s'" % name)
        else:
            raise Exception("Unable to find expense with name '%s' and parent '%s'" % (name, parent.name))

    # get the expense from our tree, this then includes depth and whether it has children
    # in the context of this season
    season_expenses = season.get_expense_tree()
    for season_expense in season_expenses:
        if season_expense.id == expense.id:
            return season_expense

    raise Exception("The expense '%s' is not a configured expense for the %s season" % (expense.name, season.name))

def strip_currency(name):
    match = re.match("^(.*?)\(.*?\)\s*$", name, re.DOTALL | re.MULTILINE)
    if match:
        return match.group(1).strip()
    else:
        return name

def get_cash_use(season, name):
    name = strip_currency(name.strip())
    try:
        cashuse = CashUse.objects.get(name=name)
    except:
        raise Exception("Unable to find cash use with name '%s'" % name)

    if not season.cash_uses.filter(pk=cashuse.pk):
        raise Exception("The cash use '%s' is not a configured cash use for the %s season" % (cashuse.name, season.name))

    return cashuse

def get_cash_source(season, name):
    name = strip_currency(name.strip())
    try:
        cashsource = CashSource.objects.get(name=name)
    except:
        raise Exception("Unable to find cash source with name '%s'" % name)

    if not season.cash_sources.filter(pk=cashsource.pk):
        raise Exception("The cash source '%s' is not a configured cash source for the %s season" % (cashsource.name, season.name))

    return cashsource

def get_farmer_payment(season, name):
    name = strip_currency(name.strip())
    try:
        farmer_payment = FarmerPayment.objects.get(name=name)
    except:
        raise Exception("Unable to find farmer payment with name '%s'" % name)

    if not season.farmer_payments.filter(farmer_payment=farmer_payment):
        raise Exception("The farmer payment '%s' is not a configured farmer payment for the %s season" % (farmer_payment.name, season.name))

    return farmer_payment

def parse_decimal(value, default_to_zero=True):
    if not value.strip():
        if default_to_zero:
            return Decimal(0)
        else:
            return None
    else:
        # strip $ signs and commas
        value = value.replace(',', '').replace('$', '')

        try:
            return Decimal(value)
        except:
            raise Exception("Invalid numeric value '%s'" % value)

def get_expense_depth(label):
    match = re.match("^( *)(.*?)$", label, re.DOTALL | re.MULTILINE)
    if match:
        depth = len(match.group(1)) / 4
        label = match.group(2)

        match = re.match("^(.*?)\s*\(([^\(\)]+)\)\s*$", label, re.DOTALL | re.MULTILINE)
        if match:
            return (depth, match.group(1), match.group(2))
        else:
            return (depth, label, None)
    else: # pragma: no cover
        return label

def build_closures(season, rows, user):
    """
    Iterates our first column, making sure everything there is known, and populating an 
    array with callbacks for each row.
    """
    closures = []

    section = None

    buyers = []
    expenses = []

    sale_index = 0
    expense_index = 0
    expense_path = [None, None, None, None, None, None]

    for row in rows:
        if not row or not row[0].strip():
            closures.append(None)
            continue

        (label, slug) = parse_label(row[0])

        # strip our slugs down
        if slug: slug = slug.strip()

        if slug == 'name':
            def set_wetmill(ctx, name):
                ctx['wetmill'] = get_wetmill(country=ctx['season'].country, name=name)

                # remove any existing report
                Report.objects.filter(season=ctx['season'], wetmill=ctx['wetmill']).delete()

                # create our new report
                ctx['report'] = Report.objects.create(season=ctx['season'], wetmill=ctx['wetmill'],
                                                      created_by=user, modified_by=user)
            closures.append(set_wetmill)

        elif slug == 'csp':
            def set_csp(ctx, name):
                ctx['csp'] = get_csp(name)
                ctx['wetmill'].set_csp_for_season(ctx['season'], ctx['csp'])
            closures.append(set_csp)

        elif slug == 'farmers':
            def set_farmers(ctx, farmers):
                ctx['report'].farmers = parse_decimal(farmers, False)
            closures.append(set_farmers)

        elif slug == 'capacity':
            def set_capacity(ctx, capacity):
                ctx['report'].capacity = parse_decimal(capacity, False)
            closures.append(set_capacity)

        elif slug == 'cherry_mem':
            def set_cherry_mem(ctx, kilos):
                ctx['report'].cherry_production_by_members = parse_decimal(kilos, False)
            closures.append(set_cherry_mem)
            
        elif label.strip() == 'Production':
            section = 'prod'
            def init_prod(ctx, nothing):
                ctx['production'] = dict()
            closures.append(init_prod)

        elif slug == 'prod' or (section == 'prod' and slug is None):
            section = 'prod'
            grade = get_grade(season, label)

            if not grade.is_parent:
                def make_set_prod(grade):
                    def set_prod(ctx, kilos):
                        ctx['production'][grade] = volume=parse_decimal(kilos)
                    return set_prod

                closures.append(make_set_prod(grade))
            else:
                def make_check_empty(grade):
                    def check_empty(ctx, value):
                        if value.strip():
                            raise Exception("Invalid value '%s' for grade '%s', parent grades may not have values." % 
                                            (value, grade.name))
                    return check_empty
                closures.append(make_check_empty(grade))

        elif slug == 'sales_kg':
            section = 'sales_kg'

            def init_sales(ctx, nothing):
                ctx['sales'] = []
            closures.append(init_sales)
            
        elif section == 'sales_kg' and slug is None:
            buyer_grade = parse_buyer_grade(label)
            grade = get_grade(season, buyer_grade[1])
            buyer = dict(label=label, name=buyer_grade[0], grade=grade)
            buyers.append(buyer)

            def make_set_volume(buyer):
                def set_volume(ctx, kilos):
                    ctx['sales'].append(dict(buyer=buyer['name'], grade=buyer['grade'], volume=parse_decimal(kilos, False)))
                return set_volume

            closures.append(make_set_volume(buyer))

        elif slug == 'sales_rev':
            section = 'sales_rev'
            sale_index = 0
            closures.append(None)

        elif section == 'sales_rev' and slug is None:
            buyer = buyers[sale_index]
            if label != buyer['label']:
                raise Exception("Invalid sale revenue row, revenue label '%s' does not match volume label '%s'" % (label, buyer['label']))

            def make_set_revenue(idx):
                def set_revenue(ctx, revenue):
                    ctx['sales'][idx]['revenue'] = parse_decimal(revenue, False)
                return set_revenue

            closures.append(make_set_revenue(sale_index))
            sale_index += 1

        elif slug == 'sales_exc':
            section = 'sales_exc'
            sale_index = 0
            closures.append(None)

        elif section == 'sales_exc' and slug is None:
            buyer = buyers[sale_index]
            if label != buyer['label']:
                raise Exception("Invalid sale exchange rate row, exchange rate label '%s' does not match volume label '%s'" % (label, buyer['label']))

            def make_set_exchange(idx):
                def set_exchange(ctx, exchange):
                    ctx['sales'][idx]['exchange_rate'] = parse_decimal(exchange, False)
                return set_exchange

            closures.append(make_set_exchange(sale_index))
            sale_index += 1

        elif slug == 'sales_type':
            section = 'sales_type'
            sale_index = 0
            closures.append(None)

        elif section == 'sales_type' and slug is None:
            buyer = buyers[sale_index]
            if label != buyer['label']:
                raise Exception("Invalid sales type row, sales type label '%s' does not match volume label '%s'" % (label, buyer['label']))

            def make_set_type(idx):
                def set_type(ctx, sales_type):
                    if sales_type: sales_type = sales_type.strip()
                    if sales_type and (sales_type.lower() != 'fob' and sales_type.lower() != 'fot' and sales_type.lower() != 'loc'):
                        raise Exception("Invalid sales type: '%s'" % sales_type)
                    ctx['sales'][idx]['sale_type'] = sales_type.upper()
                return set_type
                    
            closures.append(make_set_type(sale_index))
            sale_index += 1

        elif slug == 'sales_adj':
            section = 'sales_adj'
            sale_index = 0
            closures.append(None)

        elif section == 'sales_adj' and slug is None:
            buyer = buyers[sale_index]
            if label != buyer['label']:
                raise Exception("Invalid sales adjustment row, sales adjustment label '%s' does not match volume label '%s'" % (label, buyer['label']))

            def make_set_adjustment(idx):
                def set_adjustment(ctx, adjustment):
                    ctx['sales'][idx]['adjustment'] = parse_decimal(adjustment, False)
                return set_adjustment

            closures.append(make_set_adjustment(sale_index))
            sale_index += 1

        elif slug == 'working_cap':
            def set_working_capital(ctx, value):
                ctx['report'].working_capital = parse_decimal(value, False)
            closures.append(set_working_capital)

        elif slug == 'working_cap_repaid':
            def set_working_capital_repaid(ctx, value):
                ctx['report'].working_capital_repaid = parse_decimal(value, False)
            closures.append(set_working_capital_repaid)

        elif slug == 'misc_revenue':
            def set_misc_revenue(ctx, value):
                ctx['report'].miscellaneous_revenue = parse_decimal(value, False)
            closures.append(set_misc_revenue)

        elif slug == 'exp':
            section = 'exp'
            (depth, name, curr) = get_expense_depth(label)
            expense = get_expense(season, None, name)
            expense_path[depth+1] = expense
            expenses.append(expense)

            def init_expenses(ctx, value):
                if not 'expenses' in ctx:
                    ctx['expenses'] = dict()

                if value.strip():
                    raise Exception("Invalid value '%s' for expense '%s', parent expenses may not have values." % 
                                    (value, expense.name))
            closures.append(init_expenses)

        elif section == 'exp' and slug is None:
            (depth, name, curr) = get_expense_depth(label)
            parent = expense_path[depth]
            expense = get_expense(season, parent, name)
            expense_path[depth+1] = expense

            if not expense.is_parent:
                def make_set_expense(exp, currency):
                    def set_expense(ctx, value):
                        if currency and currency.find("Exchange") == 0:
                            ctx['expenses'][exp]['exchange_rate'] = parse_decimal(value, False)
                        else:
                            ctx['expenses'][exp] = dict(value=parse_decimal(value))
                    return set_expense
                closures.append(make_set_expense(expense, curr))
            else:
                def make_check_empty(expense):
                    def check_empty(ctx, value):
                        if value.strip():
                            raise Exception("Invalid value '%s' for expense '%s', parent expenses may not have values." % 
                                            (value, expense.name))
                    return check_empty
                closures.append(make_check_empty(expense))

        elif slug == 'cash_use':
            cash_use = get_cash_use(season, label)

            def make_set_cash_use(cash_use):
                def set_cash_use(ctx, value):
                    ctx['cash_uses'][cash_use] = parse_decimal(value, False)
                return set_cash_use

            closures.append(make_set_cash_use(cash_use))

        elif slug == 'cash_source':
            cash_source = get_cash_source(season, label)

            def make_set_cash_source(cash_source):
                def set_cash_source(ctx, value):
                    ctx['cash_sources'][cash_source] = parse_decimal(value, False)
                return set_cash_source

            closures.append(make_set_cash_source(cash_source))

        elif slug == 'farmer_payment':
            section = 'farmer_payment'
            farmer_payment = get_farmer_payment(season, label)
            closures.append(None)

        elif section == 'farmer_payment' and slug is None:
            def make_set_farmer_payment(farmer_payment, label):
                def set_farmer_payment(ctx, value):
                    if not farmer_payment in ctx['farmer_payments']:
                        ctx['farmer_payments'][farmer_payment] = dict()

                    if label.find("Non-Members") >= 0:
                        ctx['farmer_payments'][farmer_payment]['non'] = parse_decimal(value, True)

                    elif label.find("Members") >= 0:
                        ctx['farmer_payments'][farmer_payment]['mem'] = parse_decimal(value, True)

                    elif label.find("Per Kilo") >= 0:
                        ctx['farmer_payments'][farmer_payment]['all'] = parse_decimal(value, True)
                return set_farmer_payment

            closures.append(make_set_farmer_payment(farmer_payment, label))

        else:
            raise Exception("Unknown row in CSV import: '%s'" % row[0])

    return closures

def import_column(season, closures, rows, col, user):
    ctx = dict(season=season, cash_uses={}, cash_sources={}, farmer_payments={})
    
    for (index, row) in enumerate(rows):
        closure = closures[index]
        if closure:
            closure(ctx, rows[index][col])

    report = ctx['report']
    local = season.country.currency
    usd = Currency.objects.get(currency_code='USD')

    # first add our production
    for grade in ctx['production'].keys():
        volume = ctx['production'][grade]
        if not volume is None:
            report.production.create(grade=grade, volume=volume, created_by=user, modified_by=user)

    # now our sales
    if 'sales' in ctx:
        for sale in ctx['sales']:
            currency = local
            exchange_rate = None
            adjustment = None
            
            if not sale['exchange_rate'] is None:
                currency = usd
                exchange_rate = sale['exchange_rate']

            if not sale['adjustment'] is None:
                adjustment = sale['adjustment']

            if sale['volume']:
                if sale['revenue'] is None:
                    raise Exception("Missing revenue for sale to '%s'." % sale['buyer'])

                if sale['sale_type'] is None: #pragma: no cover
                    raise Exception("Missing sale type for sale to '%s', must be one of 'FOB', 'FOT' or 'LOC'" % sale['buyer'])

                # calculate our price, simple division
                price = sale['revenue'] / sale['volume'];
                new_sale = report.sales.create(buyer=sale['buyer'], sale_type=sale['sale_type'], price=price,
                                               date=datetime.now(),
                                               currency=currency, exchange_rate=exchange_rate, adjustment=adjustment,
                                               created_by=user, modified_by=user)
                new_sale.components.create(grade=sale['grade'], volume=sale['volume'],
                                           created_by=user, modified_by=user)

    # expenses
    for expense in ctx['expenses'].keys():
        values = ctx['expenses'][expense]
        exchange_rate = None
        if 'exchange_rate' in values and values['exchange_rate']:
            exchange_rate = values['exchange_rate']

        if not values['value'] is None:
            report.expenses.create(expense=expense, value=values['value'], exchange_rate=exchange_rate,
                                   created_by=user, modified_by=user)
    # cash sources
    for cash_source in ctx['cash_sources'].keys():
        value = ctx['cash_sources'][cash_source]
        report.cash_sources.create(cash_source=cash_source,
                                   value=value,
                                   created_by=user, modified_by=user)

    # cash uses
    for cash_use in ctx['cash_uses'].keys():
        value = ctx['cash_uses'][cash_use]
        report.cash_uses.create(cash_use=cash_use,
                                value=value,
                                created_by=user, modified_by=user)

    # farmer payments
    for payment in ctx['farmer_payments'].keys():
        values = ctx['farmer_payments'][payment]
        report.farmer_payments.create(farmer_payment=payment, 
                                      member_per_kilo=values.get('mem', None),
                                      non_member_per_kilo=values.get('non', None), 
                                      all_per_kilo=values.get('all', None), 
                                      created_by=user, modified_by=user)

    # attempt to finalize it
    report.finalize()

    # save our report
    report.save()

    return ctx

def import_season(season, csv_file, user, logger=None):
    from django.db import transaction
    transaction.commit()    

    reports = []

    rows = []
    reader = csv.reader(open(csv_file, 'rU'))
    for row in reader:
        rows.append(row)

    try:
        # add each wetmill one at a time
        if len(rows) > 0 and len(rows[0]) > 1:

            closures = build_closures(season, rows, user)
            results = []

            # add each column 
            for col in range(1, len(rows[0])):
                if rows[0]:
                    if logger: logger.write("Processing data for '%s'\n" % rows[0][col])
                    result = import_column(season, closures, rows, col, user)
                    reports.append(result['report'])

    except Exception as e:
        import sys, traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()

        if logger:
            logger.write("\nError Details:\n\n")
            logger.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

        # if an errors occurs, roll back any part of our import
        transaction.rollback()
        raise e

    return reports

def rows_to_csv(rows):
    try:
        from cStringIO import StringIO
    except ImportError: # pragma: no cover
        from StringIO import StringIO

    output_buffer = StringIO()
    writer = csv.writer(output_buffer)
    for row in rows:
        writer.writerow(row)
    
    return output_buffer.getvalue()

def build_sample_rows(season):
    """
    Returns a 2D array of strings that represents a sample CSV
    for import of a Season's items
    """
    PAD = "    "
    rows = []

    currency = season.country.currency.currency_code

    # wetmill attributes
    rows.append(("Name [name]", "Wetmill1", "Wetmill2"))
    rows.append(("CSP [csp]",))
    rows.append(("Number of Farmers [farmers]",))
    rows.append(("Capacity (KG) [capacity]",))

    rows.append(("",))

    # production grades
    rows.append(("Production",))

    if season.has_members:
        rows.append(("Cherry - Members (KG) [cherry_mem]",))

    for grade in season.get_grade_tree():
        suffix = ""
        if grade.depth == 0:
            suffix = " [prod]"

        if grade.is_parent:
            label = "%s%s%s" % (PAD * grade.depth, grade.full_name, suffix)
        else:
            label = "%s%s (KG)%s" % (PAD * grade.depth, grade.full_name, suffix)
        rows.append((label,))

    rows.append(("",))

    # sales 
    rows.append(("Sales (KG) [sales_kg]",))
    for i in range(20):
        rows.append(("Buyer %d" % (i+1), ))
    rows.append(("",))        

    rows.append(("Sales Revenue (%s or USD) [sales_rev]" % currency,))
    for i in range(20):
        rows.append(("Buyer %d" % (i+1), ))
    rows.append(("",))

    rows.append(("Sales Exchange Rate (%s) [sales_exc]" % currency,))
    for i in range(20):
        rows.append(("Buyer %d" % (i+1), ))
    rows.append(("",))        

    rows.append(("Sales Type (FOB or FOT) [sales_type]",))
    for i in range(20):
        rows.append(("Buyer %d" % (i+1), ))
    rows.append(("",))        

    rows.append(("Sales Adjustment (USD) [sales_adj]",))
    for i in range(20):
        rows.append(("Buyer %d" % (i+1), ))
    rows.append(("",))        

    # season attributes
    rows.append(("Working Capital (%s) [working_cap]" % currency, ))
    rows.append(("Working Capital Repaid (%s) [working_cap_repaid]" % currency, ))

    if season.has_misc_revenue:
        rows.append(("Miscellaneous Revenue (%s) [misc_revenue]" % currency, ))

    # expenses
    for expense in season.get_expense_tree():
        if expense.depth == 0:
            rows.append(("",))

        suffix = ""
        if expense.depth == 0:
            suffix = " [exp]"

        if expense.is_parent:
            rows.append(("%s%s%s" % (PAD * expense.depth, expense.name, suffix),))

        else:
            if expense.in_dollars:
                rows.append(("%s%s (USD)%s" % (PAD * expense.depth, expense.name, suffix),))
                rows.append(("%s%s (Exchange %s)%s" % (PAD * expense.depth, expense.name, currency, suffix),))
            else:
                rows.append(("%s%s (%s)%s" % (PAD * expense.depth, expense.name, currency, suffix),))

    # cash sources
    rows.append(("",))
    for cashsource in season.get_cash_sources():
        rows.append(("%s (%s) [cash_source]" % (cashsource.name, currency), ))

    # cash uses
    rows.append(("",))
    for cashuse in season.get_cash_uses():
        rows.append(("%s (%s) [cash_use]" % (cashuse.name, currency), ))

    # farmer payments
    for payment in season.get_farmer_payments():
        rows.append(("",))

        rows.append(("%s [farmer_payment]" % payment.name, ))

        if payment.applies_to == 'ALL':
            rows.append((PAD + "Per Kilo (%s/KG Cherry)" % currency, ))
        
        if payment.applies_to == 'BOT' or payment.applies_to == 'MEM':
            rows.append((PAD + "Members (%s/KG Cherry)" % currency, ))

        if payment.applies_to == 'BOT' or payment.applies_to == 'NON':
            rows.append((PAD + "Non-Members (%s/KG Cherry)" % currency, ))

    return rows
        
    


    
        
