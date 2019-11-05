from smartmin.views import *
from .models import *
from django.core.urlresolvers import reverse
from expenses.models import Expense
from grades.models import Grade
from standards.models import Standard, StandardCategory
from cashuses.models import CashUse

import re

class SeasonCRUDL(SmartCRUDL):
    model = Season
    actions = ('create', 'clone', 'update', 'list')
    permissions = True

    class Create(SmartCreateView):
        success_url = 'id@seasons.season_update'
        fields = ('name', 'country', 'exchange_rate', 'default_adjustment',
                  'has_local_sales', 'has_members', 'has_misc_revenue', 'farmer_income_baseline', 'fob_price_baseline')

        def derive_initial(self):
            initial = super(SeasonCRUDL.Create, self).derive_initial()
            if self.request.method == 'GET' and self.request.REQUEST.get('country', None):
                initial['country'] = Country.objects.get(id=self.request.REQUEST['country'])

            if self.request.method == 'GET' and self.request.REQUEST.get('name', None):
                initial['name'] = self.request.REQUEST['name']

            return initial

    class Clone(SmartCreateView):
        success_url = 'id@seasons.season_update'
        fields = ('name', 'country')

        def pre_process(self, request, *args, **kwargs):
            """
            Overloaded.. if they are posting and the country they picked has no season, then we take
            them to the full blown create page
            """
            response = super(SeasonCRUDL.Clone, self).pre_process(request, *args, **kwargs)

            if not response:
                # if there is no previous season for this country, we need to 
                # take them to the full create page
                if request.method == 'POST' and request.REQUEST['country'] and request.REQUEST['name']:
                    country = Country.objects.filter(pk=request.REQUEST['country'])
                    if country:
                        previous_season = Season.get_last_country_season(country[0])

                        # no previous seasons?  they need to go to the full season initialize view
                        if not previous_season:
                            return HttpResponseRedirect(reverse('seasons.season_create') + 
                                                        "?country=%s&name=%s" % (request.REQUEST['country'], request.REQUEST['name']))

        def pre_save(self, obj):
            """
            Overloaded so we set our required fields from our previous seasons
            """
            obj = super(SeasonCRUDL.Clone, self).pre_save(obj)
            obj.clone_from_last()
            return obj

        def save_m2m(self):
            """
            Overloaded so that we can inherit our settings from the last season in this country
            """
            super(SeasonCRUDL.Clone, self).save_m2m()
            self.object.clone_m2m_from_last()

    class Update(SmartUpdateView):
        success_url = '@seasons.season_list'        
        fields = ('is_active', 'name', 'country', 'has_local_sales', 'has_members', 
                  'has_misc_revenue', 'exchange_rate', 'default_adjustment',
                  'farmer_income_baseline', 'fob_price_baseline',
                  'farmer_payment_left', 'farmer_payment_right', 'cherry_ratio_left', 'cherry_ratio_right',
                  'total_costs_left', 'total_costs_right', 'sale_price_left', 'sale_price_right' )

        def build_checkbox_fields(self, form, name, items):
            fields = []

            for item in items:
                field_name = '%s__%d' % (name, item.id)
                item.field_name = field_name
                fields.append(item)
                
                field = forms.BooleanField(label=item.name, required=False)
                form.fields.insert(len(form.fields), field_name, field)

            return fields

        def build_grade_fields(self, form):
            fields = []

            for grade in Grade.get_grade_tree(is_active=True):
                field_name = 'grade__%d' % grade.id
                grade.field_name = field_name

                field = forms.BooleanField(label="", required=False)
                form.fields.insert(len(form.fields), field_name, field)

                # only add top grade checkboxes to green grades which have no children
                if not grade.has_children and grade.kind == 'GRE':
                    top_field_name = 'grade__%d__top' % grade.id
                    grade.top_field_name = top_field_name
                
                    field = forms.BooleanField(label="", required=False)
                    form.fields.insert(len(form.fields), top_field_name, field)

                fields.append(grade)

            return fields

        def build_expense_fields(self, form):
            fields = []

            for expense in Expense.get_expense_tree(is_active=True):
                field_name = 'expense__%d' % expense.id
                expense.field_name = field_name

                field = forms.BooleanField(label="", required=False)
                form.fields.insert(len(form.fields), field_name, field)

                fields.append(expense)

                if expense.is_parent and expense.depth == 0:
                    collapse_field_name = 'expense__%d__collapse' % expense.id
                    expense.collapse_field_name = collapse_field_name

                    field = forms.BooleanField(label="", required=False)
                    form.fields.insert(len(form.fields), collapse_field_name, field)

            return fields

        def build_payment_fields(self, form):
            fields = []

            for payment in FarmerPayment.objects.filter(is_active=True):
                field_name = 'payment__%d' % (payment.id)
                payment.field_name = field_name
                fields.append(payment)
                
                CHOICES = HAS_MEMBERS_FORM_PAYMENT_CHOICES
                if not self.object.has_members:
                    CHOICES = NO_MEMBERS_FORM_PAYMENT_CHOICES
                
                field = forms.ChoiceField(CHOICES, label=payment.name, required=False)
                form.fields.insert(len(form.fields), field_name, field)

            return fields

        def get_form(self, *args):
            form = super(SeasonCRUDL.Update, self).get_form(*args)

            standards = Standard.objects.filter(is_active=True)
            self.standard_fields = self.build_checkbox_fields(form, 'standard', standards)
            
            cashsources = CashSource.objects.filter(is_active=True)
            self.cashsource_fields = self.build_checkbox_fields(form, 'cashsource', cashsources)

            cashuses = CashUse.objects.filter(is_active=True)
            self.cashuse_fields = self.build_checkbox_fields(form, 'cashuse', cashuses)

            self.expense_fields = self.build_expense_fields(form)
            self.grade_fields = self.build_grade_fields(form)
            self.payment_fields = self.build_payment_fields(form)

            return form

        def derive_initial(self, *args):
            initial = super(SeasonCRUDL.Update, self).derive_initial(*args)

            for expense in self.object.get_expenses():
                initial['expense__%d' % expense.expense.id] = True
                initial['expense__%d__collapse' % expense.expense.id] = expense.collapse

            for grade in self.object.get_grades():
                initial['grade__%d' % grade.grade.id] = True
                initial['grade__%d__top' % grade.grade.id] = grade.is_top_grade

            for standard in self.object.standards.all():
                initial['standard__%d' % standard.id] = True

            for cashsource in self.object.get_cash_sources():
                initial['cashsource__%d' % cashsource.id] = True

            for cashuse in self.object.get_cash_uses():
                initial['cashuse__%d' % cashuse.id] = True

            for payment in self.object.get_farmer_payments():
                initial['payment__%d' % payment.id] = payment.applies_to

            return initial

        def save_m2m(self):
            self.object.standards.clear()
            self.object.cash_sources.clear()
            self.object.cash_uses.clear()

            SeasonFarmerPayment.objects.filter(season=self.object).delete()
            SeasonExpense.objects.filter(season=self.object).delete()
            SeasonGrade.objects.filter(season=self.object).delete()

            clean = self.form.cleaned_data

            for field in self.form.fields:
                match = re.match('expense__(\d+)', field)
                if match and clean[field]:
                    collapse_name = '%s__collapse' % field
                    collapse = collapse_name in clean and clean[collapse_name]

                    expense = Expense.objects.get(pk=match.group(1))

                    self.object.add_expense(expense, collapse)

                    # walk up our tree, making sure all parents are also marked active
                    parent = expense.parent
                    while parent:
                        collapse_name = 'expense__%d__collapse' % parent.id
                        collapse = collapse_name in clean and clean[collapse_name]

                        self.object.add_expense(parent, collapse)
                        parent = parent.parent

                match = re.match('^grade__(\d+)$', field)
                if match and clean[field]:
                    top_field = "%s__top" % field
                    is_top = top_field in clean and clean[top_field]

                    grade = Grade.objects.get(pk=match.group(1))

                    self.object.add_grade(grade, is_top)

                    # walk up our tree, making sure all parents are also marked active
                    parent = grade.parent
                    while parent:
                        top_field = "grade__%d__top" % parent.id
                        is_top = top_field in clean and clean[top_field]
                        self.object.add_grade(parent, is_top)
                        parent = parent.parent

                match = re.match('standard__(\d+)', field)
                if match and clean[field]:
                    standard = Standard.objects.get(pk=match.group(1))
                    self.object.standards.add(standard)

                match = re.match('cashsource__(\d+)', field)
                if match and clean[field]:
                    cashsource = CashSource.objects.get(pk=match.group(1))
                    self.object.add_cash_source(cashsource)

                match = re.match('cashuse__(\d+)', field)
                if match and clean[field]:
                    cashuse = CashUse.objects.get(pk=match.group(1))
                    self.object.add_cash_use(cashuse)

                match = re.match('payment__(\d+)', field)
                if match and clean[field] and clean[field] != 'XXX':
                    payment = FarmerPayment.objects.get(pk=match.group(1))
                    self.object.add_farmer_payment(payment,
                                                   applies_to=clean[field])


        def get_context_data(self, *args, **kwargs):
            context_data = super(SeasonCRUDL.Update, self).get_context_data(*args, **kwargs)
            context_data['attribute_fields'] = ('is_active', 'name', 'country', 'has_local_sales', 
                                                'has_members', 'has_misc_revenue', 'exchange_rate', 'default_adjustment',
                                                'farmer_income_baseline', 'fob_price_baseline', )
            context_data['expense_fields'] = self.expense_fields
            context_data['grade_fields'] = self.grade_fields
            context_data['standard_fields'] = self.standard_fields
            context_data['cashsource_fields'] = self.cashsource_fields
            context_data['standard_categories'] = StandardCategory.objects.all()
            context_data['cashuse_fields'] = self.cashuse_fields
            context_data['payment_fields'] = self.payment_fields

            return context_data
    
    class List(SmartListView):
        fields = ('name', 'country', 'is_finalized', 'created_by')
        field_config = { 'is_finalized': dict(label="Finalized") }
        default_order = ('country__name', '-name')
