from .models import *
from smartmin.views import *
from django import forms
from util.fields import TreeModelChoiceField
from django.utils.translation import ugettext_lazy as _

class ExpenseForm(forms.ModelForm):
    parent = TreeModelChoiceField(Expense, Expense.get_expense_tree, required=False)

    def clean_parent(self):
        """
        Validates that the parent set is valid
        """
        value = self.cleaned_data['parent']

        if value:
            # check self parenting
            if value == self.instance:
                raise forms.ValidationError(_("Expense cannot be the parent of itself"))

            # check parent of a child
            parent = value.parent
            while parent:
                if parent == self.instance:
                    raise forms.ValidationError(_("Expense cannot have one of its children as its parent"))
                parent = parent.parent

        return value

    class Meta:
        model = Expense

class ExpenseCRUDL(SmartCRUDL):
    model = Expense
    actions = ('create', 'update', 'list')
    permissions = True

    class Create(SmartCreateView):
        fields = ('parent', 'name', 'in_dollars', 'is_advance', 'include_in_credit_report', 'calculated_from', 'order')
        form_class = ExpenseForm

    class Update(SmartUpdateView):
        fields = ('is_active', 'parent', 'name', 'in_dollars', 'is_advance', 'include_in_credit_report', 'calculated_from', 'order')
        form_class = ExpenseForm

        def post_save(self, obj):
            # activating a child implies activating its parents
            if obj.is_active:
                expense = obj
                while expense.parent is not None:
                    expense.parent.is_active = True
                    expense.parent.save()
                    expense = expense.parent
            # deactivating a parent implies deactivating its child tree
            else:
                expense_nodes = obj.get_child_tree()
                for expense_node in expense_nodes:
                    expense_node.is_active = False
                    expense_node.save()
            return obj

    class List(SmartListView):
        fields = ('name', 'parent', 'include_in_credit_report')
        default_order = ('parent__order', 'parent__name', 'order', 'name')

        def get_context_data(self, **kwargs):
            context = super(ExpenseCRUDL.List, self).get_context_data(**kwargs)
            context['sorted_expenses'] = Expense.get_expense_tree()
            return context
