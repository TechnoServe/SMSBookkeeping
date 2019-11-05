from django.db import models
from smartmin.models import SmartModel
from django.utils.translation import ugettext as _

class Expense(SmartModel):
    CALCULATED_LEGENDS = { 'FREIGHT': _("Freight and Insurance was adjusted for FOT to FOB") }
    CALCULATED_CHOICES = (('NONE', _("Not calculated, entered manually")),
                          ('FREIGHT', _("Calculated freight and insurance")))

    parent = models.ForeignKey('self', null=True, blank=True, verbose_name=_("Parent"),
                               help_text=_("The parent this expense belongs to"))
    name = models.CharField(max_length=200, verbose_name=_("Name"),
                            help_text=_("Name this expense"))
    in_dollars = models.BooleanField(default=False, verbose_name=_("In Dollars"),
                                     help_text=_("Whether this expense is recorded in US Dollars and therefore require an exchange rate when entered"))
    is_advance = models.BooleanField(default=False, verbose_name=_("In Advance"),
                                     help_text=_("Whether this expense is considered an advance.  Used for calculating advance totals in PDF reports"))
    calculated_from = models.CharField(max_length=7, choices=CALCULATED_CHOICES, default='NONE', verbose_name=_("Calculated From"),
                                       help_text=_("Whether the value for this expense is calculated, and if so, how so."))
    order = models.IntegerField(max_length=2, verbose_name=_("Order"),
                                help_text=_("The order this expense will displayed in list, smaller orders come first"))
    include_in_credit_report = models.BooleanField(default=False, verbose_name=_("Include in Credit Report"),
                                                   help_text=_("Whether to include this expense in the credit report"))

    def get_calculated_legend(self):
        """
        Returns any legend text associated with this expense.  This only occurs if the expense is
        calculated somehow.
        """
        if self.calculated_from != 'NONE':
            return self.CALCULATED_LEGENDS.get(self.calculated_from, _("Calculated Value"))
        else:
            return None

    def has_children(self):
        """
        Returns whether this expense has any children
        """
        return Expense.objects.filter(parent=self, is_active=True).count() > 0

    def get_child_tree(self, **filters):
        """
        Returns children of this expense
        """
        return Expense.get_expense_tree(parent=self, **filters)

    @classmethod
    def _add_children(cls, expenses, parent, **filters):
        children = Expense.objects.filter(parent=parent).order_by('order')
        if filters:
            children = children.filter(**filters)

        parent.is_parent = len(children) > 0

        for child in children:
            child.depth = parent.depth + 1
            expenses.append(child)
            Expense._add_children(expenses, child, **filters)

    @classmethod
    def get_expense_tree(cls, parent=None, **filters):
        expense_tree = []
        expenses = Expense.objects.filter(parent=parent).order_by('order')
        if filters:
            expenses = expenses.filter(**filters)

        depth = 0
        if parent:
            depth = getattr(parent, 'depth', -1) + 1
            parent.is_parent = len(expenses) > 0

        for expense in expenses:
            expense.depth = depth
            expense_tree.append(expense)
            Expense._add_children(expense_tree, expense, **filters)

        return expense_tree

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('order',)
        unique_together = ('parent', 'name')
