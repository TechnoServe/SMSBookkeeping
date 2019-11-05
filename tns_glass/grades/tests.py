from django.test import TestCase
from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import Grade

class GradeTest(TNSTestCase):

    def test_ordering(self):
        self.add_grades()

        grades = Grade.get_grade_tree()
        self.assertEquals(self.cherry, grades[0])
        self.assertEquals(0, grades[0].depth)

        self.assertEquals(self.parchment, grades[1])
        self.assertEquals(0, grades[1].depth)

        self.assertEquals(self.green, grades[2])
        self.assertEquals(0, grades[2].depth)

        self.assertEquals(self.green15, grades[3])
        self.assertEquals(1, grades[3].depth)

        self.assertEquals(self.green13, grades[4])
        self.assertEquals(1, grades[4].depth)

        self.assertEquals(self.low, grades[5])
        self.assertEquals(1, grades[5].depth)

        self.assertEquals(self.ungraded, grades[6])
        self.assertEquals(2, grades[6].depth)

        self.login(self.admin)
        response = self.client.get(reverse('grades.grade_list'))
        grades = response.context['sorted_grades']

        self.assertEquals(self.cherry, grades[0])        
        self.assertEquals(self.parchment, grades[1])
        self.assertEquals(self.green, grades[2])
        self.assertEquals(self.green15, grades[3])
        self.assertEquals(self.green13, grades[4])
        self.assertEquals(self.low, grades[5])
        self.assertEquals(self.ungraded, grades[6])
        # make green inactive
        self.green15.is_active = False
        self.green15.save()

        grades = Grade.get_grade_tree(is_active=True)
        self.assertEquals(6, len(grades))


    def test_parents(self):
        self.add_grades()
        self.login(self.admin)

        update_url = reverse('grades.grade_update', args=[self.green.id])

        # parent cannot be itself
        post_data = dict(name="Green", order='0', kind='GRE', parent=self.green.id)
        response = self.client.post(update_url, post_data)
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertContains(response, "Grade cannot be the parent of itself")

        # parent cannot be a child
        post_data['parent'] = self.ungraded.id
        response = self.client.post(update_url, post_data)
        self.assertEquals(1, len(response.context['form'].errors))
        self.assertContains(response, "Grade cannot have one of its children as its parent")        

        # make sure the parent choices only include top grades
        response = self.client.get(update_url)
        choices = [choice for choice in response.context['form'].fields['parent'].choices]

        # 7 grades possible for parent grades (cherry, parchment, green, green15, green13, low grades) and 'None'
        self.assertEquals(7, len(choices))

    def test_crudl(self):
        # check permissions
        response = self.client.get(reverse('grades.grade_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)

        response = self.client.get(reverse('grades.grade_create'))
        self.assertFalse('name_en_us' in response.context['form'].fields)

        post_data = dict(name="Green", order=0, kind='GRE')
        self.assertPost(reverse('grades.grade_create'), post_data)
        green = Grade.objects.get(name="Green")

        post_data = dict(name="15+", parent=green.id, order='0', kind='PAR')
        response = self.client.post(reverse('grades.grade_create'), post_data)
        self.assertEquals(1, len(response.context['form'].errors))

        post_data['kind'] = 'GRE'
        self.assertPost(reverse('grades.grade_create'), post_data)
        green15 = Grade.objects.get(name="15+")

        response = self.client.get(reverse('grades.grade_update', args=[green15.id]))
        self.assertFalse('name_en_us' in response.context['form'].fields)

        post_data['parent'] = ""
        self.assertPost(reverse('grades.grade_update', args=[green15.id]), post_data)
        green15 = Grade.objects.get(pk=green15.id)
        self.assertEquals(None, green15.parent)

        self.assertEquals('%s' % (green15.name), '%s' % green15)

    def test_full_name(self):
        self.add_grades()

        self.assertEquals("Green", self.green.full_name)
        self.assertEquals("Green - Screen 15+", self.green15.full_name)

        self.assertEquals(self.green, Grade.from_full_name("Green"))
        self.assertEquals(self.green, Grade.from_full_name(" green  "))

        self.assertIsNone(Grade.from_full_name("Not There"))

        self.assertEquals(self.green15, Grade.from_full_name("Green - Screen 15+"))
        self.assertEquals(self.green15, Grade.from_full_name(" green - SCREEN  15+  "))
        self.assertEquals(self.green15, Grade.from_full_name(" green-SCREEN  15+  "))
