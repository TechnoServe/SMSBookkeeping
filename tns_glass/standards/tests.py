from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from .models import *

class StandardCategoryTest(TNSTestCase):
    def test_crudl(self):
        # check permissions
        response = self.client.get(reverse('standards.standardcategory_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)

        response = self.client.get(reverse('standards.standardcategory_create'))
        self.assertFalse('name_en_us' in response.context['form'].fields)

        post_data = dict(name='Standard Category One',
                         acronym="SCO",
                         order=1)
        
        self.assertPost(reverse('standards.standardcategory_create'), post_data)
        standardcategory = StandardCategory.objects.get(name='Standard Category One')
        self.assertEqual(standardcategory.acronym, 'SCO')

        response = self.client.get(reverse('standards.standardcategory_update', args=[standardcategory.id]))
        self.assertFalse('name_en_us' in response.context['form'].fields)

        update_url = reverse('standards.standardcategory_update', args=[standardcategory.id])
        
        post_data['name'] = "Standard Category Kweri"
        self.assertPost(update_url, post_data)

        standardcategory = StandardCategory.objects.get(pk=standardcategory.pk)
        self.assertEquals("Standard Category Kweri", standardcategory.name)

        category_one = StandardCategory.objects.create(name="Category One",acronym="CO",order=5,created_by=self.admin,modified_by=self.admin)
        category_two = StandardCategory.objects.create(name="Category Two",acronym="CT",order=2,created_by=self.admin,modified_by=self.admin)

        response = self.client.get(reverse('standards.standardcategory_list'))
        categories = response.context['standardcategory_list']
        self.assertEquals(self.sre_category, categories[0])
        self.assertEquals(standardcategory, categories[1])
        self.assertEquals(category_two, categories[2])
        self.assertEquals(category_one, categories[3])

        self.assertEquals(standardcategory.name, str(standardcategory))


class StandardTest(TNSTestCase):
    def test_crudl(self):
        # check permissions
        response = self.client.get(reverse('standards.standard_list'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)

        response = self.client.get(reverse('standards.standard_create'))
        self.assertFalse('name_en_us' in response.context['form'].fields)

        post_data = dict(name="Earnings Records",
                         category = self.ohs_category.id,
                         kind='MR',
                         order=1)
        
        self.assertPost(reverse('standards.standard_create'), post_data)
        standard = Standard.objects.get(name='Earnings Records')

        response = self.client.get(reverse('standards.standard_update', args=[standard.id]))
        self.assertFalse('name_en_us' in response.context['form'].fields)

        update_url = reverse('standards.standard_update', args=[standard.id])
        response = self.client.get(update_url)
        
        post_data['name'] = "Earnings Record"
        self.assertPost(update_url, post_data)

        standard = Standard.objects.get(pk=standard.pk)
        self.assertEquals("Earnings Record", standard.name)

        
        standard_one = Standard.objects.create(name="Standard One", 
                                               category=self.sre_category,
                                               kind='MR', 
                                               order=5,
                                               created_by=self.admin,
                                               modified_by=self.admin)

        standard_two = Standard.objects.create(name="Standard Two", 
                                               category=self.ohs_category, 
                                               kind='BP', 
                                               order=2, 
                                               created_by=self.admin, 
                                               modified_by=self.admin)

        standard_three = Standard.objects.create(name="Standard Three", 
                                                 category=self.sre_category,
                                                 kind='BP',
                                                 order=12,
                                                 created_by=self.admin, 
                                                 modified_by=self.admin)

        standard_four = Standard.objects.create(name="Standard Four",
                                                category=self.sre_category,
                                                kind='MR',
                                                order=0,
                                                created_by=self.admin, 
                                                modified_by=self.admin)

        response = self.client.get(reverse('standards.standard_list'))
        self.assertIn('SRE5', response.content)
        standards = response.context['standard_list']
        
        self.assertEquals(standard_four, standards[0])
        self.assertEquals(standard_one, standards[1])
        self.assertEquals(standard_three, standards[2])
        self.assertEquals(standard, standards[3])
        self.assertEquals(standard_two, standards[4])

        self.assertEquals("%s%d - %s" % (standard.category.acronym, standard.order, standard.name), str(standard))
        self.assertEquals("%s%d" % (standard.category.acronym, standard.order), standard.acronym())

