from django.test import TestCase
from tns_glass.tests import TNSTestCase
from django.core.urlresolvers import reverse
from grades.models import *
from standards.models import *
from expenses.models import *
from cashuses.models import *
from cashsources.models import *
from farmerpayments.models import *
from .models import *

class TranslationTestCase(TNSTestCase):

    def setUp(self):
        super(TranslationTestCase, self).setUp()
        Grade.objects.all().delete()
        Standard.objects.all().delete()
        StandardCategory.objects.all().delete()
    
    def test_translations(self):
        # no access by default
        response = self.client.get(reverse('translate_index'))
        self.assertRedirect(response, reverse('users.user_login'))

        self.login(self.admin)
        response = self.client.get(reverse('translate_index'))
        self.assertEquals(200, response.status_code)
        self.assertContains(response, "Kinyarwanda")
        self.assertContains(response, "Kenyan Swahili")
        self.assertContains(response, "Tanzanian Swahili")
        self.assertContains(response, "Amharic")

        response = self.client.get(reverse('rosetta-language-selection', args=['rw', '0']))
        self.assertRedirect(response, reverse('rosetta-home'))

    def test_get_translated_models(self):
        translated = get_translatable_models()
        self.assertEquals(12, len(translated))

    def test_get_foreign_languages(self):
        langs = get_foreign_languages()
        self.assertEquals(5, len(langs))
        codes = [lang[0] for lang in langs]
        self.assertTrue('ke_sw' in codes)
        self.assertTrue('tz_sw' in codes)
        self.assertTrue('rw' in codes)
        self.assertTrue('am' in codes)
        self.assertTrue('es' in codes)

    def test_get_language_name(self):
        self.assertEqual('Kinyarwanda', get_language_name('rw'))

    def add_category(self):
        # add a new model type, bringing our total to 4
        self.category = StandardCategory.objects.create(name="Environment", order=1, 
                                                        created_by=self.admin, modified_by=self.admin)

    def assertStats(self, stats, lang, total, translated, progress):
        self.assertEquals(lang, stats.code)
        self.assertEquals(total, stats.total)
        self.assertEquals(translated, stats.translated)
        self.assertEquals(progress, stats.progress())

    def test_get_translation_stats_for_class(self):
        # no objects, nothing to translate
        stats = get_translation_stats('rw', Grade)
        self.assertStats(stats, 'rw', 0, 0, 0)

        # add some grades, now three
        self.add_grades()
        stats = get_translation_stats('rw', Grade)
        self.assertStats(stats, 'rw', 7, 0, 0)

        # add a translation, now 1/3 translated
        self.green13.name_rw = "Ikawa Yumye"
        self.green13.save()
        stats = get_translation_stats('rw', Grade)
        self.assertStats(stats, 'rw', 7, 1, 14)

    def test_translation_stats(self):
        # no objects, nothing to translate
        stats = get_translation_stats('rw')
        self.assertStats(stats, 'rw', 0, 0, 0)

        # add the grades, now seven things to translate
        self.add_grades()
        stats = get_translation_stats('rw')
        self.assertStats(stats, 'rw', 7, 0, 0)

        # add a new model type, bringing our total to 4
        self.add_category()

        stats = get_translation_stats('rw')
        self.assertStats(stats, 'rw', 8, 0, 0)

        # add a translation
        self.green13.name_rw = "Ikawa Yumye"
        self.green13.save()
        
        # we now have one of our models translated
        stats = get_translation_stats('rw')
        self.assertStats(stats, 'rw', 8, 1, 12)

    def test_get_translatable_records(self):
        records = get_translatable_records('rw')
        self.assertEquals(0, len(records))

        # add grades
        self.add_grades()

        cherry_key = '%s__name__%d' % ('grade', self.cherry.id)

        records = get_translatable_records('rw')
        self.assertEquals(7, len(records))
        object_keys = [record.key for record in records]
        self.assertTrue(cherry_key in object_keys)
        self.assertEquals(cherry_key, object_keys[0])

        # test all the fields on cherry
        self.assertEquals(self.cherry, records[0].object)
        self.assertEquals(cherry_key, records[0].key)
        self.assertEquals("Grade", records[0].type)
        self.assertEquals("name", records[0].field)
        self.assertEquals("name_rw", records[0].translated_field)
        self.assertEquals("Cherry", records[0].original)
        self.assertEquals(None, records[0].translated)
        
        # add a new model type, bringing our total to 4
        self.add_category()
        category_key = '%s__name__%d' % ('standardcategory', self.category.id)

        records = get_translatable_records('rw')
        self.assertEquals(8, len(records))
        object_keys = [record.key for record in records]
        self.assertTrue(cherry_key in object_keys)
        self.assertTrue(category_key in object_keys)
        self.assertEquals(cherry_key, object_keys[0])

        records = get_translatable_records('rw', translated=True)
        self.assertEquals(0, len(records))

        records = get_translatable_records('rw', translated=False)
        self.assertEquals(8, len(records))
        
        self.cherry.name_rw = "Ikawa Yumye"
        self.cherry.save()
        
        records = get_translatable_records('rw', translated=True)
        object_keys = [record.key for record in records]
        self.assertEquals(1, len(records))
        self.assertTrue(cherry_key in object_keys)
        self.assertEquals("Ikawa Yumye", records[0].translated)

        records = get_translatable_records('rw', translated=False)
        object_keys = [record.key for record in records]
        self.assertEquals(7, len(records))
        self.assertFalse(cherry_key in object_keys)

    def test_db_translations(self):
        db_url = reverse('translate_db', args=['rw'])

        # not logged in, so can't translate
        response = self.client.get(db_url)
        self.assertRedirect(response, reverse('users.user_login'))        

        # this time should work
        self.login(self.admin)
        response = self.client.get(db_url)

        # nothing to translate
        self.assertEquals(0, len(response.context['page_obj'].object_list))

        # add our grades and category
        self.add_grades()
        self.add_category()

        # 8 things to translate now
        response = self.client.get(db_url)
        self.assertEquals(8, len(response.context['page_obj'].object_list))

        records = get_translatable_records('rw')
        post_data = {}
        post_data[records[0].key] = "Ikawa Yumye"
        response = self.client.post(db_url, post_data)

        self.assertEquals(200, response.status_code)
        records = get_translatable_records('rw')
        self.assertEquals("Ikawa Yumye", records[0].translated)

        response = self.client.get(db_url + "?filter=all")
        self.assertEquals(8, len(response.context['page_obj'].object_list))        

        response = self.client.get(db_url + "?filter=translated")
        self.assertEquals(1, len(response.context['page_obj'].object_list))        

        response = self.client.get(db_url + "?filter=untranslated&page=1")
        self.assertEquals(7, len(response.context['page_obj'].object_list))        
        
        
