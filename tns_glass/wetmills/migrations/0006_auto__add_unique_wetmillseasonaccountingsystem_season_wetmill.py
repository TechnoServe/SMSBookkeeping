# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding unique constraint on 'WetmillSeasonAccountingSystem', fields ['season', 'wetmill']
        db.create_unique(u'wetmills_wetmillseasonaccountingsystem', ['season_id', 'wetmill_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'WetmillSeasonAccountingSystem', fields ['season', 'wetmill']
        db.delete_unique(u'wetmills_wetmillseasonaccountingsystem', ['season_id', 'wetmill_id'])


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 25, 12, 42, 25, 416232)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 25, 12, 42, 25, 415732)'}),
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
        },
        u'wetmills.wetmillcspseason': {
            'Meta': {'ordering': "('-season__name', 'csp__name', 'wetmill__name')", 'unique_together': "(('wetmill', 'season'),)", 'object_name': 'WetmillCSPSeason'},
            'csp': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['csps.CSP']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        },
        u'wetmills.wetmillimport': {
            'Meta': {'ordering': "('-modified_on',)", 'object_name': 'WetmillImport'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'wetmills_wetmillimport_creations'", 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'csv_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_log': ('django.db.models.fields.TextField', [], {}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'wetmills_wetmillimport_modifications'", 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'task_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'})
        },
        u'wetmills.wetmillseasonaccountingsystem': {
            'Meta': {'ordering': "('-season__name', 'wetmill__name', 'accounting_system')", 'unique_together': "(('wetmill', 'season'),)", 'object_name': 'WetmillSeasonAccountingSystem'},
            'accounting_system': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['seasons.Season']"}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wetmills.Wetmill']"})
        }
    }

    complete_apps = ['wetmills']
