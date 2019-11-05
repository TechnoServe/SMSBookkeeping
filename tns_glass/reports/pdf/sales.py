from ..models import Report
from decimal import Decimal
from reports.pdf.currencyvalue import CurrencyValue as CV, CV_ZERO

class SalesRow(object):
    
    def __init__(self, buyer, grades, sale_type, volume, price, fot_price, fob_price, freight, revenue, is_total=False):
        self.buyer = buyer
        self.grades = grades
        self.sale_type = sale_type

        self.volume = volume
        self.price = price
        self.fot_price = fot_price
        self.fob_price = fob_price
        self.revenue = revenue
        self.freight = freight
        self.is_total = is_total

    def get_buyer_display(self, buyer_name=None):
        if not buyer_name:
            buyer_name = self.buyer

        display = "%s (%s)" % (buyer_name, self.grade_string())
        if self.sale_type == 'FOT':
            display += "*"

        return display

    def grade_string(self):
        if len(self.grades) > 1: # pragma: no cover
            # determine if we can shorten our grade string... we can shorten it in the case
            # where all our grades share the same parent
            same_parent = True
            parent = self.grades[0].parent
            for grade in self.grades[1:]:
                if grade.parent != parent:
                    same_parent = False
                    break

            if same_parent and parent: 
                return self.grades[0].parent.name + " - " + ", ".join([grade.name for grade in self.grades])
            else:
                return ", ".join(grade.full_name for grade in self.grades)
        elif len(self.grades):
            return self.grades[0].full_name
        else: # pragma: no cover
            return ""

    def get_depth1_grade(self):
        for grade in self.grades:
            return SalesBox.get_depth1_parent(grade)

class SalesBox(object):

    def __init__(self, report, currency):
        self.report = report
        self.currency = currency

        self.build_export_rows()
        self.build_local_rows()

        self.build_totals()

    @classmethod
    def get_depth1_parent(cls, grade):
        if grade.parent and grade.parent.parent:
            return cls.get_depth1_parent(grade.parent)

        return grade

    def build_totals(self):
        total_export = self.export_rows[-1]
        total_local = self.local_rows[-1]
        
        self.total_revenue = total_export.revenue + total_local.revenue
        self.total_freight = total_export.freight + total_local.freight

        # average fot sale price
        self.fot_price = total_export.fot_price
        self.total_export_volume = total_export.volume

    def build_total_row(self, rows):
        total_volume = Decimal("0")
        total_revenue = CV(Decimal("0"))
        total_freight = CV(Decimal("0"))

        total_fob = CV(Decimal("0"))
        total_fot = CV(Decimal("0"))

        for row in rows:
            total_volume += row.volume
            total_revenue += row.revenue
            total_freight += row.freight

            total_fob += (row.volume * row.fob_price)
            total_fot += (row.volume * row.fot_price)

        fot_price = total_fot / total_volume
        fob_price = total_fob / total_volume
        price = total_revenue / total_volume

        return SalesRow("Total Sales", [], "", total_volume, price, fot_price, fob_price, 
                        total_freight, total_revenue, is_total=True)

    def build_row(self, buyer, price, grades, sale_type, adjustment, volume):
        if adjustment is None:
            adjustment = CV(self.report.season.default_adjustment, self.report.season.exchange_rate)
        else:
            adjustment = CV(adjustment, self.report.season.exchange_rate)

        if sale_type == 'FOT':
            fot_price = price
            if fot_price.as_local(self.report.season.exchange_rate) > Decimal(0):
                fob_price = fot_price + adjustment
            else:
                fob_price = CV_ZERO
            freight = adjustment * volume
            revenue = fob_price * volume

        elif sale_type == 'FOB':
            fob_price = price
            fot_price = fob_price - adjustment
            if fot_price.as_local(self.report.season.exchange_rate) < Decimal(0):
                fot_price = CV_ZERO
            freight = CV_ZERO
            revenue = fob_price * volume

        elif sale_type == 'LOC':
            fob_price = CV_ZERO
            fot_price = CV_ZERO
            price = price
            adjustment = CV_ZERO
            freight = CV_ZERO
            revenue = price * volume
        else: # pragma: no cover
            raise Exception("Invalid sale type: '%s' for sale to '%s" % (sale_type, buyer))

        return SalesRow(buyer, grades, sale_type, volume, price, fot_price, fob_price, freight, revenue)        
    
    def build_export_rows(self):
        self.export_rows = self.build_rows(self.report.sales.exclude(sale_type='LOC'))
        self.export_rows.append(self.build_total_row(self.export_rows))

    def build_local_rows(self):
        self.local_rows = self.build_rows(self.report.sales.filter(sale_type='LOC'))
        self.local_rows.append(self.build_total_row(self.local_rows))

    def build_rows(self, sales):
        rows = []
        combination_sales = []

        # for each sale
        for sale in sales:
            volume = Decimal(0)
            grades = []

            # whether all the grades in this sale are depth 2.. if so, then this sale
            # will be combined with other sales that are all depth2 if by the same buyer
            can_be_combined = sale.components.count() > 0
            depth1_parent = -1

            for component in sale.components.all():
                grade = component.grade
                if not grade.parent or not grade.parent.parent:
                    can_be_combined = False
                else:
                    grade_depth1_parent = self.get_depth1_parent(grade)
                    if depth1_parent == -1:
                        depth1_parent = grade_depth1_parent

                    if depth1_parent != grade_depth1_parent:
                        can_be_combined = False

                volume += component.volume
                if not component.grade in grades:
                    grades.append(component.grade)
            

            row = self.build_row(sale.buyer, CV(sale.price, sale.exchange_rate), 
                                 grades, sale.sale_type, sale.adjustment, volume)

            if can_be_combined:
                combination_sales.append(row)
            else:
                rows.append(row)

        # now we try to combine all the depth2 sales
        depth2_buyers = dict()
        for sale in combination_sales:
            sale_key = "%s_%s_%s" % (sale.buyer, sale.sale_type, sale.get_depth1_grade().id)
            
            if sale_key in depth2_buyers:
                depth2_buyers[sale_key].append(sale)
            else:
                depth2_buyers[sale_key] = [sale]

        for sales in depth2_buyers.values():
            total_volume = Decimal(0)
            total_fot_revenue = CV_ZERO
            total_fob_revenue = CV_ZERO
            total_freight = CV_ZERO
            depth1_grade = None

            fot_price = CV_ZERO
            fob_price = CV_ZERO

            for sale in sales:
                total_volume += sale.volume
                total_fot_revenue += (sale.volume * sale.fot_price)
                total_fob_revenue += (sale.volume * sale.fob_price)
                total_freight += sale.freight

                if depth1_grade is None:
                    for grade in sale.grades:
                        depth1_grade = self.get_depth1_parent(grade)
                        break

            if total_volume > Decimal("0"):
                fot_price = total_fot_revenue / total_volume
                fob_price = total_fob_revenue / total_volume

            # we don't call build_row here because build_row side-effects our total forex loss and
            # those have already been accounted for above
            combined_row = SalesRow(sales[0].buyer, [depth1_grade], sales[0].sale_type, 
                                    total_volume, fob_price, fot_price, fob_price, total_freight, total_fob_revenue)

            rows.append(combined_row)

        return rows

    def get_export_rows(self):
        return self.export_rows

    def get_local_rows(self):
        return self.local_rows
        
