from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import *

class ExpenseTest(TNSTestCase):

    def test_model(self):
        self.add_expenses()

        tree = Expense.get_expense_tree()
        self.assertEquals(7, len(tree))

        self.assertEquals(self.expense_washing_station, tree[0])
        self.assertEquals(0, tree[0].depth)
        self.assertTrue(tree[0].has_children())

        self.assertEquals(self.expense_cherry_advance, tree[1])
        self.assertEquals(1, tree[1].depth)
        self.assertFalse(tree[1].has_children())

        self.assertEquals(self.expense_other, tree[2])
        self.assertEquals(1, tree[2].depth)
        self.assertTrue(tree[2].has_children())

        self.assertEquals(self.expense_taxes, tree[3])
        self.assertEquals(2, tree[3].depth)
        self.assertFalse(tree[3].has_children())

        self.assertEquals(self.expense_unexplained, tree[4])
        self.assertEquals(2, tree[4].depth)
        self.assertFalse(tree[4].has_children())

        # test filtering by parent
        tree = Expense.get_expense_tree(self.expense_capex)
        self.assertEquals(1, len(tree))

        self.assertEquals(self.expense_capex_interest, tree[0])
        self.assertEquals(0, tree[0].depth)
        self.assertFalse(tree[0].has_children())

        # test filtering arbitrarily
        tree = Expense.get_expense_tree(self.expense_washing_station, is_advance=True)
        self.assertEquals(1, len(tree))
        self.assertEquals(self.expense_cherry_advance, tree[0])

    def test_crudl(self):
        # check permissions
        response = self.client.get(reverse('expenses.expense_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)
        Expense.objects.all().delete()

        post_data = dict(name="Expense Hatari", order=1, calculated_from='NONE')
        
        self.assertPost(reverse('expenses.expense_create'), post_data)
        expense = Expense.objects.get(name='Expense Hatari')

        update_url = reverse('expenses.expense_update', args=[expense.id])
        response = self.client.get(update_url)
        
        post_data['name'] = "Expense Mistical"
        self.assertPost(update_url, post_data)

        expense = Expense.objects.get(pk=expense.pk)
        self.assertEquals("Expense Mistical", expense.name)

        parent_one = Expense.objects.create(name="Parent One", order=2,
                                            created_by=self.admin, modified_by=self.admin)
        parent_two = Expense.objects.create(name="Parent two", order=3,
                                            created_by=self.admin, modified_by=self.admin)
        parent_three = Expense.objects.create(name="Parent three", order=1,
                                              created_by=self.admin, modified_by=self.admin)

        p1_child_one = Expense.objects.create(name="P1 Child One", parent=parent_one, order=2,
                                              created_by=self.admin, modified_by=self.admin)
        p1_child_two = Expense.objects.create(name="P1 Child two", parent=parent_one, order=1,
                                              created_by=self.admin, modified_by=self.admin)
        p1_child_three = Expense.objects.create(name="P1 Child three", parent=parent_one, order=3,
                                                created_by=self.admin, modified_by=self.admin)

        p1_c1_grand_one = Expense.objects.create(name="P1 C1 Grand Child One", parent=p1_child_one, order=3,
                                                 created_by=self.admin, modified_by=self.admin)
        p1_c1_grand_two = Expense.objects.create(name="P1 C1 Grand Child Two", parent=p1_child_one, order=2,
                                                 created_by=self.admin, modified_by=self.admin)
        p1_c1_grand_three = Expense.objects.create(name="P1 C1 Grand Child Three", parent=p1_child_one, order=1,
                                                   created_by=self.admin, modified_by=self.admin)


        update_url = reverse('expenses.expense_update', args=[parent_one.id])
        post_data = dict(name="Parent One", order=1, calculated_from='NONE', parent=parent_one.id)
        response = self.client.post(update_url, post_data)

        # should fail, can't have itself as parent
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertContains(response, "Expense cannot be the parent of itself")

        post_data = dict(name="Parent One", order=1, calculated_from='NONE', parent=p1_child_one.id)
        response = self.client.post(update_url, post_data)

        # should fail, can't have parent of one of it's children
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertContains(response, "Expense cannot have one of its")

        response = self.client.get(reverse('expenses.expense_list'))
        expenses = response.context['sorted_expenses']
        
        self.assertEquals(expense, expenses[0])
        self.assertEquals(parent_three, expenses[1])
        self.assertEquals(parent_one, expenses[2])
        self.assertEquals(p1_child_two, expenses[3])
        self.assertEquals(p1_child_one, expenses[4])
        self.assertEquals(p1_c1_grand_three, expenses[5])
        self.assertEquals(p1_c1_grand_two, expenses[6])
        self.assertEquals(p1_c1_grand_one, expenses[7])
        self.assertEquals(p1_child_three, expenses[8])
        self.assertEquals(parent_two, expenses[9])
        
        self.assertIn(expense.name, str(expense))

        # deactivate a parent and check if its children are deactivated
        update_url = reverse('expenses.expense_update', args=[parent_one.id])
        post_data = dict(name="Parent One", order=2, calculated_from='NONE')
        self.assertPost(update_url, post_data)

        parent_one = Expense.objects.get(pk=parent_one.pk)

        self.assertFalse(parent_one.is_active)
        for expense in parent_one.get_child_tree():
            self.assertFalse(expense.is_active)

        # activate a parent should not affect its children
        update_url = reverse('expenses.expense_update', args=[parent_one.id])
        post_data = dict(name="Parent One", order=2, is_active=1, calculated_from='NONE')
        self.assertPost(update_url, post_data)

        parent_one = Expense.objects.get(pk=parent_one.pk)
        self.assertTrue(parent_one.is_active)
        self.assertFalse(parent_one.has_children())
        for expense in parent_one.get_child_tree():
            self.assertFalse(expense.is_active)

        # activate a child of deactivated parent should activate it parents
        parent_one.is_active = False
        parent_one.save()
        update_url = reverse('expenses.expense_update', args=[p1_c1_grand_one.id])
        post_data = dict(name="P1 C1 Grand Child One", parent=p1_child_one.id, order=3, is_active=1, calculated_from='NONE')
        self.assertPost(update_url, post_data)

        expense = Expense.objects.get(pk=p1_c1_grand_one.pk)
        self.assertTrue(expense.is_active)
        while expense.parent is not None:
            self.assertTrue(expense.parent.is_active)
            expense = expense.parent

        # deactivate a child and its parent should not be affected
        update_url = reverse('expenses.expense_update', args=[p1_c1_grand_one.id])
        post_data = dict(name="P1 C1 Grand Child One", parent=p1_child_one.id, order=3, calculated_from='NONE')
        self.assertPost(update_url, post_data)

        expense = Expense.objects.get(pk=p1_c1_grand_one.pk)
        self.assertFalse(expense.is_active)
        while expense.parent is not None:
            self.assertTrue(expense.parent.is_active)
            expense = expense.parent
