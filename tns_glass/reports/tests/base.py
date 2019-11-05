from tns_glass.tests import TNSTestCase
from expenses.models import Expense
from grades.models import Grade
from reports.models import Report, Sale
from datetime import datetime
from decimal import Decimal
from seasons.models import SeasonGrade, Season, SeasonFarmerPayment
from locales.models import Currency, Country, Province
from wetmills.models import Wetmill
from cashuses.models import CashUse
from cashsources.models import CashSource
from farmerpayments.models import FarmerPayment

class PDFTestCase(TNSTestCase):
    """
    Base class that holds a lot of bootstrapping methods for the report object
    we are testing.
    """
    def setUp(self):
        super(PDFTestCase, self).setUp()
        self.report = Report.get_for_wetmill_season(self.nasho, self.rwanda_2010, self.admin)
        self.report.farmers = 100
        self.report.capacity = Decimal("10000")
        self.report.save()
        self.season = self.rwanda_2010
        self.nasho.set_csp_for_season(self.season, self.rtc)

    def setup_ethiopia_season(self):
        self.birr = Currency.objects.create(name="Ethiopian Birr", has_decimals=True, abbreviation='Birr',
                                            created_by=self.admin, modified_by=self.admin)
        self.ethiopia = Country.objects.create(name="Ethiopia", currency=self.birr, country_code='ET', calling_code='254',
                                               created_by=self.admin, modified_by=self.admin)
        self.ethiopia_2009 = Season.objects.create(country=self.ethiopia, name="2009", has_local_sales=True,
                                                   default_adjustment=Decimal("0.20"), exchange_rate=Decimal("17.00"),
                                                   farmer_income_baseline=Decimal("100"), fob_price_baseline="1.15",
                                                   has_members=True,
                                                   created_by=self.admin, modified_by=self.admin)

        self.illubabor = Province.objects.create(country=self.ethiopia, name="Illubabor", order=0,
                                                 created_by=self.admin, modified_by=self.admin)
        self.camp_cooperative = Wetmill.objects.create(country=self.ethiopia, province=self.illubabor, name="Camp Cooperative",
                                                       created_by=self.admin, modified_by=self.admin)
        self.report = Report.get_for_wetmill_season(self.camp_cooperative, self.ethiopia_2009, self.admin)
        self.report.working_capital = Decimal("307938")
        self.report.working_capital_repaid=Decimal("0")

        self.season = self.ethiopia_2009

    def add_productions(self):
        self.add_production(self.cherry, Decimal("68654"))
        self.add_production(self.parchment, Decimal("13723"))
        self.add_production(self.green15, Decimal("8880"))
        self.add_production(self.green13, Decimal("1092"))
        self.add_production(self.low, Decimal("1063"))

    def add_production(self, grade, volume, is_top_grade=False):
        self.report.production.create(grade=grade, volume=volume,
                                      created_by=self.admin, modified_by=self.admin)

    def add_expenses(self):
        Expense.objects.all().delete()

        self.washing_expenses = self.add_expense(None, "Washing Station Expenses")
        cherry_advance = self.add_expense(self.washing_expenses, "Cherry Advance", "8128839")
        cherry_advance.is_advance = True
        cherry_advance.save()

        self.cherry_advance = cherry_advance

        self.add_expense(self.washing_expenses, "Cherry Transport", "590265")
        self.add_expense(self.washing_expenses, "Labor (Full-Time)", "605000")
        self.add_expense(self.washing_expenses, "Labor (Casual)", "996900")
        other = self.add_expense(self.washing_expenses, "Other expenses")
        self.add_expense(other, "Batteries and Lighting", "0")
        self.add_expense(other, "Coffee Bags and Strings", "10800")
        self.add_expense(other, "Dry Parchment Transport", "340000")
        self.add_expense(other, "Fuels and Oils", "136590")
        self.add_expense(other, "Local Taxes", "0")
        self.add_expense(other, "Other", "72620")
        self.add_expense(other, "Payment to Site Collector", "199596")
        self.add_expense(other, "Rental of Store", "20000")
        self.add_expense(other, "Repairs and Maintenance", "500")
        self.add_expense(other, "Stationary, Papers, Copies", "14750")
        self.add_expense(other, "Telephone Expenses", "14500")
        self.add_expense(other, "Traveling Expenses", "125300")
        self.add_expense(other, "Unexplained Expenses", "6040")

        milling = self.add_expense(None, "Milling, Marketing and Export Expenses")
        self.add_expense(milling, "Marketing Fee", "1512035")
        self.add_expense(milling, "Milling", "485794")
        self.add_expense(milling, "Hand Sorting", "207200")
        self.add_expense(milling, "Export Bagging", "148444")
        self.add_expense(milling, "Transport", "58500")

        storage = self.add_expense(milling, "Storage and Handling")
        self.add_expense(storage, "CSP Warehouse Handling", "5850")
        self.add_expense(storage, "OCIR Warehouse Handling", "11700")
        self.add_expense(storage, "Other Storage and Handling", "7605")

        gov = self.add_expense(milling, "Government Taxes, Fees and Deductions")
        self.add_expense(gov, "Fertilizer Fund Contribution", "810780")
        self.add_expense(gov, "VAT", "74880")
        self.add_expense(gov, "Other Taxes & Fees", "0")

        freight = self.add_expense(milling, "Freight and Insurance")
        self.add_expense(freight, "Incurred", "108810")
        calculated = self.add_expense(freight, "Calculated", None)
        calculated.calculated_from = 'FREIGHT'
        calculated.in_dollars = True
        calculated.save()
        
        self.add_expense(milling, "Other", "0")

        capex = self.add_expense(None, "Working Capital Financing Expenses")
        self.add_expense(capex, "Working Capital Interest", "151814")
        self.add_expense(capex, "Working Capital Fee", "112616")

        capex_fin = self.add_expense(None, "CAPEX Financing Expenses")
        repayment = self.add_expense(capex_fin, "CAPEX Principal Repayment", "2440.23", "590")
        repayment.in_dollars = True; repayment.save();

        interest = self.add_expense(capex_fin, "CAPEX Interest", "618.23", "590")
        interest.in_dollars = True; interest.save()

    def add_grades(self):
        super(PDFTestCase, self).add_grades()
        
        self.green12 = self.add_grade("Screen 12", "GRE", 0, self.low)
        self.hpc = self.add_grade("HPC", "GRE", 2, self.low)
        self.triage = self.add_grade("Triage", "GRE", 3, self.low)

        self.rwanda_2010.add_grade(self.green)
        self.rwanda_2010.add_grade(self.green15, True)
        self.rwanda_2010.add_grade(self.green13)
        self.rwanda_2010.add_grade(self.low)
        self.rwanda_2010.add_grade(self.green12)
        self.rwanda_2010.add_grade(self.hpc)
        self.rwanda_2010.add_grade(self.triage)

        self.rwanda_2010.add_grade(self.cherry)
        self.rwanda_2010.add_grade(self.parchment)

    def add_sale(self, buyer, price, currency, exchange_rate, grade, volume, sale_type='FOT'):
        sale = Sale.objects.create(buyer=buyer,
                                   price=price,
                                   report=self.report,
                                   date=datetime.now().date(),
                                   currency=currency,
                                   exchange_rate=exchange_rate,
                                   sale_type=sale_type,
                                   adjustment=None,
                                   created_by=self.admin,
                                   modified_by=self.admin)
        sale.components.create(grade=grade, volume=volume, created_by=self.admin, modified_by=self.admin)

        return sale

    def add_cash_sources(self):
        CashSource.objects.all().delete()

        self.cs_cash_due = CashSource.objects.create(name="Cash Due from CSP",
                                                     order=0, calculated_from='CDUE',
                                                     created_by=self.admin, modified_by=self.admin)
        self.cs_unused_working_cap = CashSource.objects.create(name="Unused Working Capital with Cooperative", 
                                                               order=1, calculated_from='WCAP',
                                                               created_by=self.admin, modified_by=self.admin)
        self.cs_misc_sources = CashSource.objects.create(name="Miscellaneous Sources", order=2,
                                                         created_by=self.admin, modified_by=self.admin)
        
        self.season.add_cash_source(self.cs_cash_due)
        self.season.add_cash_source(self.cs_unused_working_cap)
        self.season.add_cash_source(self.cs_misc_sources)

        self.report.cash_sources.create(cash_source=self.cs_misc_sources, value=Decimal("0"),
                                        created_by=self.admin, modified_by=self.admin)

    def add_farmer_payments(self):
        FarmerPayment.objects.all().delete()
        
        self.fp_dividend = FarmerPayment.objects.create(name="Dividend", order=0,
                                                        created_by=self.admin, modified_by=self.admin)
        self.fp_second_payment = FarmerPayment.objects.create(name="Second Payment", order=1,
                                                              created_by=self.admin, modified_by=self.admin)

        self.rwanda_2010.add_farmer_payment(self.fp_dividend, 'MEM')
        self.rwanda_2010.add_farmer_payment(self.fp_second_payment, 'BOT')

        self.report.farmer_payments.create(farmer_payment=self.fp_dividend, member_per_kilo=Decimal("22"),
                                           created_by=self.admin, modified_by=self.admin)
        self.report.farmer_payments.create(farmer_payment=self.fp_second_payment, 
                                           member_per_kilo=Decimal("30"), non_member_per_kilo=Decimal("30"),
                                           created_by=self.admin, modified_by=self.admin)

    def add_cash_uses(self):
        CashUse.objects.all().delete()

        self.cu_dividend = CashUse.objects.create(name="Dividend", order=0, 
                                                  created_by=self.admin, modified_by=self.admin)
        self.cu_second_payment = CashUse.objects.create(name="Second Payment", order=1,
                                                        created_by=self.admin, modified_by=self.admin)
        self.cu_retained_profit = CashUse.objects.create(name="Retained Profit", order=1, calculated_from='PROF',
                                                         created_by=self.admin, modified_by=self.admin)

        self.rwanda_2010.add_cash_use(self.cu_dividend)
        self.rwanda_2010.add_cash_use(self.cu_second_payment)
        self.rwanda_2010.add_cash_use(self.cu_retained_profit)

        self.report.cash_uses.create(cash_use=self.cu_second_payment, value=Decimal("1755000"),
                                     created_by=self.admin, modified_by=self.admin)
        self.report.cash_uses.create(cash_use=self.cu_dividend, value=Decimal("1528020"),
                                     created_by=self.admin, modified_by=self.admin)

    def add_sales(self):
        self.sale_rogers1 = self.add_sale("Rogers Family Co.", "3.60", self.usd, "591.10", self.green15, 660)
        self.sale_rogers2 = self.add_sale("Rogers Family Co.", "3.60", self.usd, "588.71", self.green15, 8220)
        self.sale_rogers2.adjustment = Decimal("0.16")
        self.sale_rogers2.save()
        self.sale_rwacof1 = self.add_sale("Rwacof", "1935.48", self.rwf, None, self.green13, 1092)
        self.sale_rwacof2 = self.add_sale("Rwacof", "1505.38", self.rwf, None, self.green12, 39)
        self.sale_rwacof3 = self.add_sale("Rwacof", "806.45", self.rwf, None, self.ungraded, 465)
        self.sale_rwacof4 = self.add_sale("Rwacof", "483.87", self.rwf, None, self.hpc, 386)
        self.sale_rwacof5 = self.add_sale("Rwacof", "236.56", self.rwf, None, self.triage, 173)

    def add_ethiopia_productions(self):
        self.add_grades()

        self.cherry_washed = self.add_grade("Washed", 'CHE', 0, self.cherry)
        self.cherry_natural = self.add_grade("Converted to natural", 'CHE', 1, self.cherry)
        self.cherry_natural.is_not_processed = True
        self.cherry_natural.save()

        self.parchment_milled = self.add_grade("Dry-milled", 'PAR', 0, self.parchment)
        self.parchment_local = self.add_grade("Sold locally", 'PAR', 1, self.parchment)
        self.parchment_local.is_not_processed= True
        self.parchment_local.save()

        self.jenfel = self.add_grade("Jenfel", 'UNW', 2)
        self.jenfel_milled = self.add_grade("Dry-milled", 'UNW', 0, self.jenfel)
        self.jenfel_local = self.add_grade("Sold locally", 'UNW', 1, self.jenfel)
        self.jenfel_local.is_not_processed = True
        self.jenfel_local.save()

        self.green_washed = self.add_grade("Washed", 'GRE', 0, self.green)
        self.green_naturals = self.add_grade("Naturals", 'GRE', 1, self.green)
        self.green_naturals.is_not_processed = True
        self.green_naturals.save()

        SeasonGrade.objects.filter(season=self.rwanda_2010).delete()

        self.season.add_grade(self.cherry)
        self.season.add_grade(self.cherry_washed)
        self.season.add_grade(self.cherry_natural, False)
        self.season.add_grade(self.parchment)
        self.season.add_grade(self.parchment_milled)
        self.season.add_grade(self.parchment_local, False)
        self.season.add_grade(self.jenfel)
        self.season.add_grade(self.jenfel_milled)
        self.season.add_grade(self.jenfel_local)
        self.season.add_grade(self.green)
        self.season.add_grade(self.green_washed)
        self.season.add_grade(self.green_naturals, False)

        self.report.production.all().delete()

        self.add_production(self.cherry_washed, Decimal("54788"))
        self.add_production(self.cherry_natural, Decimal("203"))

        self.add_production(self.parchment_milled, Decimal("9855"))
        self.add_production(self.parchment_local, Decimal("389"))

        self.add_production(self.jenfel_milled, Decimal("68"))
        self.add_production(self.jenfel_local, Decimal("0"))

        self.add_production(self.green_washed, Decimal("8187"))
        self.add_production(self.green_naturals, Decimal("26"))

    def add_ethiopia_sales(self):
        self.buyer_a = self.add_sale("Buyer A", "4.1448", self.usd, "17.00", self.green_washed, 7058, 'FOB')

        self.buyer_b = self.add_sale("Buyer B", "1.8623", self.usd, "17.00", self.green_washed, 1129, 'LOC')
        self.buyer_c = self.add_sale("Buyer C", "1.20", self.usd, "17.00", self.parchment_local, 300, 'LOC')
        self.buyer_d = self.add_sale("Buyer D", "1.00", self.usd, "17.00", self.parchment_local, 89, 'LOC')
        self.buyer_e = self.add_sale("Buyer E", "2.4604", self.usd, "17.00", self.green_naturals, 26, 'LOC')

    def add_ethiopia_expenses(self):
        Expense.objects.all().delete()

        self.washing_expenses = self.add_expense(None, "Washing Station Expenses")
        cherry_advance = self.add_expense(self.washing_expenses, "Cherry Advance", "265811.08")
        cherry_advance.is_advance = True
        cherry_advance.save()

        self.add_expense(self.washing_expenses, "Cherry Transport", "4744.30")
        self.add_expense(self.washing_expenses, "Labor (Full-Time)", "5544.98")
        self.add_expense(self.washing_expenses, "Labor (Casual)", "8441.45")
        self.add_expense(self.washing_expenses, "Other expenses", "22049.00")

        milling = self.add_expense(None, "Milling, Marketing and Export Expenses")
        self.add_expense(milling, "Marketing Commission", "26705.72")
        self.add_expense(milling, "Export Costs", "6214.85")
        self.add_expense(milling, "Milling Fee", "12691.73")
        self.add_expense(milling, "Transport", "785.45")

        capex = self.add_expense(None, "Working Capital Financing Expenses")
        self.add_expense(capex, "Interest Expense", "23698.57")
        self.add_expense(capex, "Bank Fees", "0")

        capex_fin = self.add_expense(None, "CAPEX Financing Expenses")
        repayment = self.add_expense(capex_fin, "CAPEX Principal Repayment", "4820.59", "17.00")
        repayment.in_dollars = True; repayment.save();

        interest = self.add_expense(capex_fin, "CAPEX Interest", "1324.16", "17.00")
        interest.in_dollars = True; interest.save()

    def add_ethiopia_cash_uses(self):
        super(PDFTestCase, self).add_cash_uses()
        self.season.add_cash_use(self.cu_dividend)
        self.report.cash_uses.create(cash_use=self.cu_dividend, value=Decimal("50184"),
                                     created_by=self.admin, modified_by=self.admin)

    def add_ethiopia_payments(self):
        super(PDFTestCase, self).add_farmer_payments()
        self.season.add_farmer_payment(self.fp_dividend, 'MEM')
        self.report.farmer_payments.create(farmer_payment=self.fp_dividend, member_per_kilo=Decimal("0.76"),
                                           created_by=self.admin, modified_by=self.admin)
        

                
