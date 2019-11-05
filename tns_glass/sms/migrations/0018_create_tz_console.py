# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        from rapidsms.models import Backend
        Backend.objects.get_or_create(name='tz_tester')

        console = Backend.objects.get(name='console')
        console.name = 'tns_tester'
        console.save()

    def backwards(self, orm):
        pass

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 7, 28, 9, 22, 7, 128749)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 7, 28, 9, 22, 7, 128186)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'cashsources.cashsource': {
            'Meta': {'ordering': "('order',)", 'object_name': 'CashSource'},
            'calculated_from': ('django.db.models.fields.CharField', [], {'default': "'NONE'", 'max_length': '4'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'cashsources_cashsource_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'cashsources_cashsource_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'cashuses.cashuse': {
            'Meta': {'object_name': 'CashUse'},
            'calculated_from': ('django.db.models.fields.CharField', [], {'default': "'NONE'", 'max_length': '4'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'cashuses_cashuse_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'cashuses_cashuse_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'csps.csp': {
            'Meta': {'ordering': "('country__name', 'name')", 'object_name': 'CSP'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'csps_csp_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'csps_csp_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'sms_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '16', 'db_index': 'True'})
        },
        u'eav.attribute': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('site', 'slug'),)", 'object_name': 'Attribute'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'datatype': ('eav.fields.EavDatatypeField', [], {'max_length': '6'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'enum_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['eav.EnumGroup']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'slug': ('eav.fields.EavSlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'eav.enumgroup': {
            'Meta': {'object_name': 'EnumGroup'},
            'enums': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['eav.EnumValue']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'eav.enumvalue': {
            'Meta': {'object_name': 'EnumValue'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        u'eav.value': {
            'Meta': {'object_name': 'Value'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['eav.Attribute']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'entity_ct': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'value_entities'", 'to': u"orm['contenttypes.ContentType']"}),
            'entity_id': ('django.db.models.fields.IntegerField', [], {}),
            'generic_value_ct': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'value_values'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'generic_value_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value_bool': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'value_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'value_enum': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'eav_values'", 'null': 'True', 'to': u"orm['eav.EnumValue']"}),
            'value_float': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_int': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'value_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'expenses.expense': {
            'Meta': {'ordering': "('order',)", 'unique_together': "(('parent', 'name'),)", 'object_name': 'Expense'},
            'calculated_from': ('django.db.models.fields.CharField', [], {'default': "'NONE'", 'max_length': '7'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'expenses_expense_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_dollars': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_advance': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'expenses_expense_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['expenses.Expense']", 'null': 'True', 'blank': 'True'})
        },
        u'grades.grade': {
            'Meta': {'ordering': "('order',)", 'unique_together': "(('parent', 'name'),)", 'object_name': 'Grade'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'grades_grade_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_not_processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'grades_grade_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['grades.Grade']"})
        },
        u'locales.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country'},
            'bounds_lat': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '6'}),
            'bounds_lng': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '6'}),
            'bounds_zoom': ('django.db.models.fields.IntegerField', [], {'default': '8'}),
            'calling_code': ('django.db.models.fields.IntegerField', [], {}),
            'country_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'locales_country_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'countries'", 'to': u"orm['locales.Currency']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'locales_country_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'national_id_format': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'phone_format': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        u'locales.currency': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Currency'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'locales_currency_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'}),
            'has_decimals': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'locales_currency_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'prefix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4', 'blank': 'True'})
        },
        u'locales.province': {
            'Meta': {'ordering': "('country__name', 'order')", 'object_name': 'Province'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'locales_province_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'locales_province_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'})
        },
        u'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        u'rapidsms.connection': {
            'Meta': {'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'rapidsms_xforms.xform': {
            'Meta': {'object_name': 'XForm'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'command_prefix': ('django.db.models.fields.CharField', [], {'default': "'+'", 'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('eav.fields.EavSlugField', [], {'max_length': '32', 'db_index': 'True'}),
            'keyword_prefix': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'response': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'response_am': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'response_en_us': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'response_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'response_rw': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'response_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'restrict_message': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'restrict_to': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'separator': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"})
        },
        u'rapidsms_xforms.xformsubmission': {
            'Meta': {'object_name': 'XFormSubmission'},
            'confirmation_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Connection']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'has_errors': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'raw': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'xform': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': u"orm['rapidsms_xforms.XForm']"})
        },
        u'seasons.season': {
            'Meta': {'ordering': "('country__name', '-name')", 'unique_together': "(('country', 'name'),)", 'object_name': 'Season'},
            'cash_sources': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cashsources.CashSource']", 'symmetrical': 'False'}),
            'cash_uses': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cashuses.CashUse']", 'symmetrical': 'False'}),
            'cherry_ratio_left': ('django.db.models.fields.DecimalField', [], {'default': '12', 'max_digits': '16', 'decimal_places': '4'}),
            'cherry_ratio_right': ('django.db.models.fields.DecimalField', [], {'default': '5', 'max_digits': '16', 'decimal_places': '4'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'seasons_season_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_adjustment': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'exchange_rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'expenses': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['expenses.Expense']", 'through': u"orm['seasons.SeasonExpense']", 'symmetrical': 'False'}),
            'farmer_income_baseline': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'farmer_payment_left': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '4'}),
            'farmer_payment_right': ('django.db.models.fields.DecimalField', [], {'default': '100', 'max_digits': '16', 'decimal_places': '4'}),
            'fob_price_baseline': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grades': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['grades.Grade']", 'through': u"orm['seasons.SeasonGrade']", 'symmetrical': 'False'}),
            'has_local_sales': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_members': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_misc_revenue': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_finalized': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'seasons_season_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'sale_price_left': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '4'}),
            'sale_price_right': ('django.db.models.fields.DecimalField', [], {'default': '10', 'max_digits': '16', 'decimal_places': '4'}),
            'standards': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['standards.Standard']", 'symmetrical': 'False'}),
            'total_costs_left': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '4'}),
            'total_costs_right': ('django.db.models.fields.DecimalField', [], {'default': '100', 'max_digits': '16', 'decimal_places': '4'})
        },
        u'seasons.seasonexpense': {
            'Meta': {'ordering': "('expense__order',)", 'unique_together': "(('season', 'expense'),)", 'object_name': 'SeasonExpense'},
            'collapse': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'expense': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['expenses.Expense']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"})
        },
        u'seasons.seasongrade': {
            'Meta': {'ordering': "('grade__order',)", 'unique_together': "(('season', 'grade'),)", 'object_name': 'SeasonGrade'},
            'grade': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['grades.Grade']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_top_grade': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"})
        },
        u'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'sms.accountant': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Accountant', '_ormbases': [u'sms.Actor']},
            u'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'accountants'", 'null': 'True', 'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.actor': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Actor'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms.Connection']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'rw'", 'max_length': '5'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'sms.amafarangasubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'AmafarangaSubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']", 'null': 'True'}),
            'advanced': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'casual_labor': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'commission': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'full_time_labor': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'opening_balance': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'other_expenses': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'other_income': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'start_of_week': ('django.db.models.fields.DateField', [], {}),
            'transport': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"}),
            'working_capital': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'})
        },
        u'sms.cashsubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'CashSubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']"}),
            'cash_advances': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'casual_wages': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry_transport_wages': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'income': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'other_cash_out': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'salaries': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            'site_collector_wages': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"}),
            'working_capital': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'})
        },
        u'sms.cherrysubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'CherrySubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']"}),
            'cash_advance': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cash_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry_paid_cash': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry_paid_credit': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cpo': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.CPO']"}),
            'credit_paid_off': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'credit_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'daylot': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.cpo': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'CPO', '_ormbases': [u'sms.Actor']},
            u'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'cpo_id': ('django.db.models.fields.IntegerField', [], {}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']", 'null': 'True', 'blank': 'True'})
        },
        u'sms.cspofficer': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'CSPOfficer', '_ormbases': [u'sms.Actor']},
            u'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'csp': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['csps.CSP']", 'null': 'True', 'blank': 'True'})
        },
        u'sms.farmer': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Farmer', '_ormbases': [u'sms.Actor']},
            u'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'farmers'", 'null': 'True', 'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.ibitumbwesubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'IbitumbweSubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']", 'null': 'True'}),
            'cash_advanced': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cash_returned': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cash_spent': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry_purchased': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'credit_cleared': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2'}),
            'credit_spent': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'report_day': ('django.db.models.fields.DateField', [], {}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.receivedsubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'ReceivedSubmission', '_ormbases': [u'sms.SMSSubmission']},
            'cupping_score': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'license_plate': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'moisture_content': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'officer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.CSPOfficer']"}),
            'parchmenta_bags': ('django.db.models.fields.IntegerField', [], {}),
            'parchmenta_kg': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'parchmentb_bags': ('django.db.models.fields.IntegerField', [], {}),
            'parchmentb_kg': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.returnsubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'ReturnSubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']"}),
            'cash': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cpo': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.CPO']"}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.shippingsubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'ShippingSubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']"}),
            'license_plate': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parchmenta_bags': ('django.db.models.fields.IntegerField', [], {}),
            'parchmenta_kg': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'parchmentb_bags': ('django.db.models.fields.IntegerField', [], {}),
            'parchmentb_kg': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.sitokisubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'SitokiSubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']", 'null': 'True'}),
            'grade_a_shipped': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_a_stored': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_b_shipped': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_b_stored': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_c_shipped': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_c_stored': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'start_of_week': ('django.db.models.fields.DateField', [], {}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.smssubmission': {
            'Meta': {'object_name': 'SMSSubmission'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'day': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rapidsms_xforms.XFormSubmission']", 'null': 'True', 'blank': 'True'})
        },
        u'sms.storesubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'StoreSubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']"}),
            'daylot': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'gradea_moved': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'gradeb_moved': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.summarysubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'SummarySubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']"}),
            'balance': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'daylot': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'paid': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            'sent': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'stored': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.twakinzesubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'TwakinzeSubmission', '_ormbases': [u'sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sms.Accountant']", 'null': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'report_day': ('django.db.models.fields.DateField', [], {}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            u'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'sms.wetmillobserver': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'WetmillObserver', '_ormbases': [u'sms.Actor']},
            u'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']", 'null': 'True', 'blank': 'True'})
        },
        u'standards.standard': {
            'Meta': {'unique_together': "(('category', 'name'),)", 'object_name': 'Standard'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['standards.StandardCategory']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'standards_standard_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'standards_standard_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'})
        },
        u'standards.standardcategory': {
            'Meta': {'object_name': 'StandardCategory'},
            'acronym': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'standards_standardcategory_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'standards_standardcategory_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'}),
            'public_display': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'wetmills.wetmill': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('country', 'name'),)", 'object_name': 'Wetmill'},
            'altitude': ('django.db.models.fields.IntegerField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'wetmills_wetmill_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '20', 'decimal_places': '16', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '20', 'decimal_places': '16', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'wetmills_wetmill_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'province': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locales.Province']"}),
            'sms_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'}),
            'sms_system': ('django.db.models.fields.CharField', [], {'default': "'2012'", 'max_length': '4', 'null': 'True'}),
            'year_started': ('django.db.models.fields.IntegerField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sms']
