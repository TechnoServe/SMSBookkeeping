from django.db import models
from django.db.models import Avg, Min, Max
from seasons.models import Season
from reports.models import Report
from decimal import Decimal
from tasks import finalize_season
from smartmin.models import SmartModel
from datetime import datetime
from django.utils.translation import ugettext_lazy as _

class FinalizeTask(SmartModel):
    season = models.ForeignKey(Season, verbose_name=_("Season"),
                               help_text=_("The season which will be finalized"))
    task_log = models.TextField(verbose_name=_("Task Log"), help_text=_("Any logging collected while finalizing this season"))
    task_id = models.CharField(null=True, max_length=64, verbose_name=_("Task Id"))

    def __unicode__(self):
        return "Finalize Task for %s" % self.season.name

    def start(self): # pragma: no cover
        result = finalize_season.delay(self)
        self.task_id = result.task_id
        self.task_log = "Starting finalization.\n"
        self.save()

    def get_status(self):
        status = 'PENDING'
        if self.task_id: # pragma: no cover
            result = finalize_season.AsyncResult(self.task_id)
            status = result.state

        return status

    def log(self, message):
        self.task_log += "%s\n" % message
        self.modified_on = datetime.now()
        self.save()

    class Meta:
        ordering = ('-modified_on',)

class SeasonMetric(models.Model):
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    slug = models.SlugField(verbose_name=_("Slug"))
    label = models.CharField(max_length=128, verbose_name=_("Label"))
    is_cost = models.BooleanField(default=True, verbose_name=_("Is Cost"))

class ReportValue(models.Model):
    report = models.ForeignKey(Report, verbose_name=_("Report"))
    metric = models.ForeignKey(SeasonMetric, verbose_name="Metric")
    value = models.DecimalField(max_digits=16, decimal_places=4, verbose_name=_("Value"), null=True)

    def get_season_values(self):
        all_values = ReportValue.objects.filter(report__season=self.report.season,
                                                metric=self.metric).aggregate(Avg('value'), Min('value'), Max('value'))

        season_values = dict(avg=all_values['value__avg'], min=all_values['value__min'], max=all_values['value__max'])

        if self.metric.is_cost:
            season_values['best'] = all_values['value__min']
        else:
            season_values['best'] = all_values['value__max']

        return season_values

    def rank(self):
        if not self.value:
            return None

        # low values are good
        if self.metric.is_cost:
            return ReportValue.objects.filter(report__season=self.report.season, metric=self.metric, 
                                              value__lt=self.value).count() + 1

        # high values are good
        else:
            return ReportValue.objects.filter(report__season=self.report.season, metric=self.metric, 
                                              value__gt=self.value).count() + 1

class SeasonAggregate(models.Model):
    season = models.ForeignKey(Season, verbose_name=_("Season"))
    slug = models.SlugField(verbose_name=_("Slug"))
    average = models.DecimalField(max_digits=16, decimal_places=4, null=True, verbose_name=_("Average"))
    lowest = models.DecimalField(max_digits=16, decimal_places=4, null=True, verbose_name=_("Lowest"))
    highest = models.DecimalField(max_digits=16, decimal_places=4, null=True, verbose_name=_("Highest"))
    best = models.DecimalField(max_digits=16, decimal_places=4, null=True, verbose_name=_("Best"))

    class Meta:
        unique_together = ('season', 'slug')

    @classmethod
    def for_season(cls, season):
        season_dict = dict()

        for aggregate in SeasonAggregate.objects.filter(season=season):
            season_dict[aggregate.slug] = aggregate

        return season_dict

    @classmethod
    def per_kilo(cls, cv, kilos, exchange):
        if not cv is None and kilos:
            in_local = cv.as_local(exchange)
            
            if not in_local is None:
                return in_local / kilos
            else: #pragma: no cover
                return None

    @classmethod
    def add_value(cls, values, slugs, slug, value, is_cost=True):
        values[slug] = value
        slugs[slug] = is_cost

    @classmethod
    def add_metric(cls, metrics, report, slug, label, value, is_cost):
        metric = metrics.get(slug, None)
        if not metric:
            metric = SeasonMetric.objects.create(season=report.season, slug=slug, label=label, is_cost=is_cost)
            metrics[slug] = metric

        ReportValue.objects.create(metric=metric, report=report, value=value)

    @classmethod
    def calculate_for_season(cls, season):
        from reports.pdf.production import ProductionBox
        from reports.pdf.sales import SalesBox
        from reports.pdf.expenses import ExpenseBox
        from reports.pdf.farmer import FarmerBox
        from reports.pdf.cash import CashBox
        from reports.models import Report

        # remove existing aggregates
        SeasonAggregate.objects.filter(season=season).delete()
        ReportValue.objects.filter(report__season=season).delete()
        SeasonMetric.objects.filter(season=season).delete()

        # aggregates are all in local currency
        currency = season.country.currency
        curr_code = currency.currency_code

        # exchange rate for this season
        exchange = season.exchange_rate
        
        # the set of keys we've seen
        slugs = dict()

        # our report metrics
        metrics = dict()

        # a list of all the report values we have accumulated
        report_values = []

        # for each finalized report
        for report in Report.objects.filter(season=season, is_finalized=True):
            # dict containing the aggregate values for this report
            values = dict()

            # calculates the metrics for this report and populates our
            # report boxes in the process
            report.calculate_metrics()

            # save our updated metrics
            report.save()

            production = report.production_box
            sales = report.sales_box
            expenses = report.expenses_box
            cash = report.cash_box
            farmer = report.farmer_box

            green = production.green_total
            cherry = production.cherry_total
            green_ratio = production.cherry_to_green_ratio

            for category in expenses.get_categories():
                cls.add_value(values, slugs, category.slug(), cls.per_kilo(category.value, green, exchange))
                cls.add_value(values, slugs, "%s__advance" % category.slug(), cls.per_kilo(category.advance_value, green, exchange))
                cls.add_value(values, slugs, "%s__non_advance" % category.slug(), cls.per_kilo(category.non_advance_value(), green, exchange))

                cls.add_metric(metrics, report, "%s__kgc" % category.slug(), "%s Expenses (%s/KgC)" % (category.name, curr_code), cls.per_kilo(category.value, cherry, exchange), True)
                cls.add_metric(metrics, report, '%s__non_advance__kgc' % category.slug(), "%s Non-Advance Expenses (%s/KgC)" % (category.name, curr_code), cls.per_kilo(category.non_advance_value(), cherry, exchange), True)

                for child in category.children:
                    cls.add_value(values, slugs, child.slug(), cls.per_kilo(child.value, green, exchange))
                    cls.add_metric(metrics, report, "%s__kgc" % child.slug(), "%s (%s/KgC)" % (child.name, curr_code), cls.per_kilo(child.value, cherry, exchange), True)

            # add in our total expenses
            cls.add_value(values, slugs, 'sales_revenue', cls.per_kilo(expenses.sales_revenue, green, exchange), False)
            cls.add_value(values, slugs, 'misc_revenue', cls.per_kilo(expenses.misc_revenue, green, exchange), False)
            cls.add_value(values, slugs, 'total_revenue', cls.per_kilo(expenses.total_revenue, green, exchange), False)
            cls.add_value(values, slugs, 'total_expenses', cls.per_kilo(expenses.total, green, exchange))

            cls.add_value(values, slugs, 'total_forex_loss', cls.per_kilo(expenses.total_forex_loss, green, exchange))
            cls.add_value(values, slugs, 'total_profit', cls.per_kilo(expenses.total_profit, green, exchange), False)
            cls.add_value(values, slugs, 'production_cost', expenses.production_cost.as_local(exchange))
            
            # cash box
            cls.add_value(values, slugs, 'cash_due', cls.per_kilo(cash.cash_due, cherry, exchange))
            cls.add_value(values, slugs, 'unused_working_capital', cls.per_kilo(cash.cash_due, cherry, exchange))

            # graphs
            cls.add_value(values, slugs, 'farmer_payment', cls.per_kilo(farmer.total_paid, cherry, exchange))
            cls.add_value(values, slugs, 'cherry_to_parchment_ratio', production.cherry_to_parchment_ratio)
            cls.add_value(values, slugs, 'parchment_to_green_ratio', production.parchment_to_green_ratio)
            cls.add_value(values, slugs, 'cherry_to_green_ratio', production.cherry_to_green_ratio)
            cls.add_value(values, slugs, 'cherry_to_top_grade_ratio', production.cherry_to_top_grade_ratio)
            cls.add_value(values, slugs, 'top_grade_percentage', production.top_grade_percentage)

            # total cherry
            cls.add_value(values, slugs, 'total_cherry', production.cherry_total, False)

            # working capital received
            cls.add_value(values, slugs, 'working_capital_received', report.working_capital)

            # sales box
            cls.add_value(values, slugs, 'fot_price', sales.fot_price.as_local(exchange))

            # metrics
            cls.add_metric(metrics, report, 'total_revenue', "Total Revenue (%s)" % curr_code, expenses.total_revenue.as_local(exchange), False)
            cls.add_metric(metrics, report, 'total_revenue__kgc', "Total Revenue (%s/KgC)" % curr_code, cls.per_kilo(expenses.total_revenue, cherry, exchange), False)

            cls.add_metric(metrics, report, 'total_expenses', "Total Expenses (%s)" % curr_code, expenses.total.as_local(exchange), True)
            cls.add_metric(metrics, report, 'total_expenses__kgc', "Total Expenses (%s/KgC)" % curr_code, cls.per_kilo(expenses.total, cherry, exchange), True)

            cls.add_metric(metrics, report, 'total_profit', "Total Profit (%s)" % curr_code, expenses.total_profit.as_local(exchange), False)
            cls.add_metric(metrics, report, 'total_profit__kgc', "Total Profit (%s/KgC)" % curr_code, cls.per_kilo(expenses.total_profit, cherry, exchange), False)

            cls.add_metric(metrics, report, 'fot_price', "FOT Price (%s/KgG)" % curr_code, sales.fot_price.as_local(exchange), False)
            cls.add_metric(metrics, report, 'fot_price_kgc', "FOT Price (%s/KgC)" % curr_code, cls.per_kilo(sales.fot_price * sales.total_export_volume, cherry, exchange), False)
            cls.add_metric(metrics, report, 'farmer_payment__sum', "Farmer Payment Sum (%s)" % curr_code, farmer.total_paid.as_local(exchange), False)

            cls.add_metric(metrics, report, 'total_revenue', "Total Revenue (%s)" % curr_code, expenses.total_revenue.as_local(exchange), False)

            cls.add_metric(metrics, report, 'total_cherry', "Total Cherry (KgC)", production.cherry_total, False)
            cls.add_metric(metrics, report, 'total_parchment', "Total Parchment (KgP)", production.parchment_total, False)
            cls.add_metric(metrics, report, 'total_green', "Total Green (KgG)", production.green_total, False)

            cls.add_metric(metrics, report, 'cherry_to_parchment_ratio', "Cherry to Parchment Ratio", production.cherry_to_parchment_ratio, True)
            cls.add_metric(metrics, report, 'parchment_to_green_ratio', "Parchment to Green Ratio", production.parchment_to_green_ratio, True)
            cls.add_metric(metrics, report, 'cherry_to_green_ratio', "Cherry to Green Ratio", production.cherry_to_green_ratio, True)
            cls.add_metric(metrics, report, 'cherry_to_top_grade_ratio', "Cherry to Top Grade Ratio", production.cherry_to_top_grade_ratio, True)
            cls.add_metric(metrics, report, 'top_grade_percentage', "Top Grade Percentage", production.top_grade_percentage, False)

            # cash uses
            for use in cash.get_uses():
                cls.add_value(values, slugs, use.slug(), cls.per_kilo(use.total, cherry, exchange), False)

            # cash sources
            for source in cash.get_sources():
                cls.add_value(values, slugs, source.slug(), cls.per_kilo(source.total, cherry, exchange), False)

            # retained profit
            cls.add_value(values, slugs, 'retained_profit', cls.per_kilo(cash.retained_profit, cherry, exchange), False)

            # farmer payments
            for row in farmer.get_rows():
                value = row.value

                # we store per kilo of green here, which we have to calculate using ratios otherwise it doesn't
                # properly take into account parchment that is not milled
                if not value is None and cherry and not green_ratio is None:
                    # calculate per kilo of cherry
                    value = value.as_local(exchange) / cherry * green_ratio

                cls.add_value(values, slugs, row.slug(), value, False)

                metric_label = "%s (%s/KgC)" % (row.label, curr_code)
                if row.row_for == 'MEM':
                    metric_label += " (Members)"
                elif row.row_for == 'NON':
                    metric_label += " (Non-Members)"
                else:
                    metric_label += " (All Farmers)"

                cls.add_metric(metrics, report, row.slug(), metric_label, cls.per_kilo(row.value, cherry, exchange), False)

            report_values.append(values)

        # now for each key, calculate the average and best
        for slug in slugs.keys():
            is_cost = slugs[slug]
            total = Decimal(0)
            count = 0
            lowest = None
            highest = None

            for report_value in report_values:
                if slug in report_value:
                    value = report_value[slug]
                    if not value is None:
                        total = total + value
                        count += 1

                        if lowest is None or value < lowest:
                            lowest = value
                            
                        if highest is None or value > highest:
                            highest = value

            # calculate our mean
            if count > 0:
                average = total / count
            else:
                average = None

            if is_cost:
                best = lowest
            else:
                best = highest

            # add our slug aggregate
            SeasonAggregate.objects.create(season=season, slug=slug, average=average, lowest=lowest, 
                                           highest=highest, best=best)


        # set our gauge limits based on our aggregates
        if 'farmer_payment' in slugs:
            agg = SeasonAggregate.objects.get(season=season, slug='farmer_payment')
            season.farmer_payment_left = agg.lowest
            season.farmer_payment_right = agg.highest
        
        if 'cherry_to_green_ratio' in slugs:
            agg = SeasonAggregate.objects.get(season=season, slug='cherry_to_green_ratio')
            season.cherry_ratio_left = agg.highest
            season.cherry_ratio_right = agg.lowest

        if 'production_cost' in slugs:
            agg = SeasonAggregate.objects.get(season=season, slug='production_cost')
            season.total_costs_left = agg.highest
            season.total_costs_right = agg.lowest

        if 'fot_price' in slugs:
            agg = SeasonAggregate.objects.get(season=season, slug='fot_price')
            season.sale_price_left = agg.lowest
            season.sale_price_right = agg.highest

        # mark our season as finalized
        season.is_finalized = True
        season.save()

        return len(report_values)

            


            
            
