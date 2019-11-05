# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        from sms.models import *
        for af in AmafarangaSubmission.objects.all():
            af.is_active = True
            af.save()

        for ib in IbitumbweSubmission.objects.all():
            ib.is_active = True
            ib.save()

        for tw in TwakinzeSubmission.objects.all():
            tw.is_active = True
            tw.save()

        for si in SitokiSubmission.objects.all():
            si.is_active = True
            si.save()

        # remove dupes by day
        for af in AmafarangaSubmission.objects.all().order_by('-pk'):
            if not AmafarangaSubmission.objects.filter(pk=af.pk):
                continue

            # find any on the same day
            for dupe in AmafarangaSubmission.objects.filter(wetmill=af.wetmill, season=af.season, start_of_week=af.start_of_week).exclude(pk=af.pk):
                dupe.active = False
                dupe.save()

        # remove dupes by day
        for si in SitokiSubmission.objects.all().order_by('-pk'):
            if not SitokiSubmission.objects.filter(pk=si.pk):
                continue

            # find any on the same day
            for dupe in SitokiSubmission.objects.filter(wetmill=si.wetmill, season=si.season, start_of_week=si.start_of_week).exclude(pk=si.pk):
                dupe.active = False
                dupe.save()

        # remove dupes by day
        for tw in TwakinzeSubmission.objects.all().order_by('-pk'):
            if not TwakinzeSubmission.objects.filter(pk=tw.pk):
                continue

            # find any on the same day
            for dupe in TwakinzeSubmission.objects.filter(wetmill=tw.wetmill, season=tw.season, report_day=tw.report_day).exclude(pk=tw.pk):
                dupe.active = False
                dupe.save()

        # remove dupes by day
        for ib in IbitumbweSubmission.objects.all().order_by('-pk'):
            if not IbitumbweSubmission.objects.filter(pk=ib.pk):
                continue

            # find any on the same day
            for dupe in IbitumbweSubmission.objects.filter(wetmill=ib.wetmill, season=ib.season, report_day=ib.report_day).exclude(pk=ib.pk):
                dupe.active = False
                dupe.save()

    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 3, 1, 15, 3, 29, 103537)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 3, 1, 15, 3, 29, 103448)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'cashsources.cashsource': {
            'Meta': {'ordering': "('order',)", 'object_name': 'CashSource'},
            'calculated_from': ('django.db.models.fields.CharField', [], {'default': "'NONE'", 'max_length': '4'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cashsource_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cashsource_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'cashuses.cashuse': {
            'Meta': {'object_name': 'CashUse'},
            'calculated_from': ('django.db.models.fields.CharField', [], {'default': "'NONE'", 'max_length': '4'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cashuse_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cashuse_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'csps.csp': {
            'Meta': {'ordering': "('country__name', 'name')", 'object_name': 'CSP'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'csp_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'csp_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'sms_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '16', 'db_index': 'True'})
        },
        'eav.attribute': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('site', 'slug'),)", 'object_name': 'Attribute'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'datatype': ('eav.fields.EavDatatypeField', [], {'max_length': '6'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'enum_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eav.EnumGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'slug': ('eav.fields.EavSlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'eav.enumgroup': {
            'Meta': {'object_name': 'EnumGroup'},
            'enums': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['eav.EnumValue']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'eav.enumvalue': {
            'Meta': {'object_name': 'EnumValue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'eav.value': {
            'Meta': {'object_name': 'Value'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eav.Attribute']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'entity_ct': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'value_entities'", 'to': "orm['contenttypes.ContentType']"}),
            'entity_id': ('django.db.models.fields.IntegerField', [], {}),
            'generic_value_ct': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'value_values'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'generic_value_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value_bool': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'value_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'value_enum': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'eav_values'", 'null': 'True', 'to': "orm['eav.EnumValue']"}),
            'value_float': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_int': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'value_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'expenses.expense': {
            'Meta': {'ordering': "('order',)", 'unique_together': "(('parent', 'name'),)", 'object_name': 'Expense'},
            'calculated_from': ('django.db.models.fields.CharField', [], {'default': "'NONE'", 'max_length': '7'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'expense_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_dollars': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_advance': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'expense_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['expenses.Expense']", 'null': 'True', 'blank': 'True'})
        },
        'grades.grade': {
            'Meta': {'ordering': "('order',)", 'unique_together': "(('parent', 'name'),)", 'object_name': 'Grade'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'grade_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_not_processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'grade_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['grades.Grade']"})
        },
        'locales.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country'},
            'bounds_lat': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '6'}),
            'bounds_lng': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '6'}),
            'bounds_zoom': ('django.db.models.fields.IntegerField', [], {'default': '8'}),
            'calling_code': ('django.db.models.fields.IntegerField', [], {}),
            'country_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'country_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'countries'", 'to': "orm['locales.Currency']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'country_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'national_id_format': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'phone_format': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'locales.currency': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Currency'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'currency_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'}),
            'has_decimals': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'currency_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'prefix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4', 'blank': 'True'})
        },
        'locales.province': {
            'Meta': {'ordering': "('country__name', 'order')", 'object_name': 'Province'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'province_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'province_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'})
        },
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.connection': {
            'Meta': {'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'rapidsms_xforms.xform': {
            'Meta': {'object_name': 'XForm'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'command_prefix': ('django.db.models.fields.CharField', [], {'default': "'+'", 'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('eav.fields.EavSlugField', [], {'max_length': '32', 'db_index': 'True'}),
            'keyword_prefix': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'response': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'response_am': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'response_en_us': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'response_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'response_rw': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'response_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'restrict_message': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'restrict_to': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'separator': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"})
        },
        'rapidsms_xforms.xformsubmission': {
            'Meta': {'object_name': 'XFormSubmission'},
            'confirmation_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'has_errors': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'raw': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'xform': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['rapidsms_xforms.XForm']"})
        },
        'seasons.season': {
            'Meta': {'ordering': "('country__name', '-name')", 'unique_together': "(('country', 'name'),)", 'object_name': 'Season'},
            'cash_sources': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cashsources.CashSource']", 'symmetrical': 'False'}),
            'cash_uses': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cashuses.CashUse']", 'symmetrical': 'False'}),
            'cherry_ratio_left': ('django.db.models.fields.DecimalField', [], {'default': '12', 'max_digits': '16', 'decimal_places': '4'}),
            'cherry_ratio_right': ('django.db.models.fields.DecimalField', [], {'default': '5', 'max_digits': '16', 'decimal_places': '4'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'season_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_adjustment': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'exchange_rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'expenses': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['expenses.Expense']", 'through': "orm['seasons.SeasonExpense']", 'symmetrical': 'False'}),
            'farmer_income_baseline': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'farmer_payment_left': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '4'}),
            'farmer_payment_right': ('django.db.models.fields.DecimalField', [], {'default': '100', 'max_digits': '16', 'decimal_places': '4'}),
            'fob_price_baseline': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grades': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['grades.Grade']", 'through': "orm['seasons.SeasonGrade']", 'symmetrical': 'False'}),
            'has_local_sales': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_members': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_misc_revenue': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_finalized': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'season_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'sale_price_left': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '4'}),
            'sale_price_right': ('django.db.models.fields.DecimalField', [], {'default': '10', 'max_digits': '16', 'decimal_places': '4'}),
            'standards': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['standards.Standard']", 'symmetrical': 'False'}),
            'total_costs_left': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '4'}),
            'total_costs_right': ('django.db.models.fields.DecimalField', [], {'default': '100', 'max_digits': '16', 'decimal_places': '4'})
        },
        'seasons.seasonexpense': {
            'Meta': {'ordering': "('expense__order',)", 'unique_together': "(('season', 'expense'),)", 'object_name': 'SeasonExpense'},
            'collapse': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'expense': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['expenses.Expense']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"})
        },
        'seasons.seasongrade': {
            'Meta': {'ordering': "('grade__order',)", 'unique_together': "(('season', 'grade'),)", 'object_name': 'SeasonGrade'},
            'grade': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['grades.Grade']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_top_grade': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'sms.accountant': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Accountant', '_ormbases': ['sms.Actor']},
            'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'accountants'", 'null': 'True', 'to': "orm['wetmills.Wetmill']"})
        },
        'sms.actor': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Actor'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'rw'", 'max_length': '5'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'sms.amafarangasubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'AmafarangaSubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'advanced': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'casual_labor': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'commission': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'full_time_labor': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'opening_balance': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'other_expenses': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'other_income': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'start_of_week': ('django.db.models.fields.DateField', [], {}),
            'transport': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"}),
            'working_capital': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'})
        },
        'sms.cashsubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'CashSubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'cash_advances': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'casual_wages': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry_transport_wages': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'income': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'other_cash_out': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'salaries': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'site_collector_wages': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"}),
            'working_capital': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'})
        },
        'sms.cherrysubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'CherrySubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'cash_advance': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cash_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry_paid_cash': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry_paid_credit': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cpo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.CPO']"}),
            'credit_paid_off': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'credit_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'daylot': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"})
        },
        'sms.cpo': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'CPO', '_ormbases': ['sms.Actor']},
            'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'cpo_id': ('django.db.models.fields.IntegerField', [], {}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']", 'null': 'True', 'blank': 'True'})
        },
        'sms.cspofficer': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'CSPOfficer', '_ormbases': ['sms.Actor']},
            'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'csp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['csps.CSP']", 'null': 'True', 'blank': 'True'})
        },
        'sms.farmer': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Farmer', '_ormbases': ['sms.Actor']},
            'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'farmers'", 'null': 'True', 'to': "orm['wetmills.Wetmill']"})
        },
        'sms.ibitumbwesubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'IbitumbweSubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'cash_advanced': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cash_returned': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cash_spent': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry_purchased': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'credit_cleared': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2'}),
            'credit_spent': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'report_day': ('django.db.models.fields.DateField', [], {}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"})
        },
        'sms.receivedsubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'ReceivedSubmission', '_ormbases': ['sms.SMSSubmission']},
            'cupping_score': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'license_plate': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'moisture_content': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'officer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.CSPOfficer']"}),
            'parchmenta_bags': ('django.db.models.fields.IntegerField', [], {}),
            'parchmenta_kg': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'parchmentb_bags': ('django.db.models.fields.IntegerField', [], {}),
            'parchmentb_kg': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"})
        },
        'sms.returnsubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'ReturnSubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'cash': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cpo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.CPO']"}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"})
        },
        'sms.shippingsubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'ShippingSubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'license_plate': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parchmenta_bags': ('django.db.models.fields.IntegerField', [], {}),
            'parchmenta_kg': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'parchmentb_bags': ('django.db.models.fields.IntegerField', [], {}),
            'parchmentb_kg': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"})
        },
        'sms.sitokisubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'SitokiSubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'grade_a_shipped': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_a_stored': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_b_shipped': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_b_stored': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_c_shipped': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'grade_c_stored': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'start_of_week': ('django.db.models.fields.DateField', [], {}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"})
        },
        'sms.smssubmission': {
            'Meta': {'object_name': 'SMSSubmission'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'day': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms_xforms.XFormSubmission']", 'null': 'True', 'blank': 'True'})
        },
        'sms.storesubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'StoreSubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'daylot': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'gradea_moved': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'gradeb_moved': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"})
        },
        'sms.summarysubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'SummarySubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'balance': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'cherry': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'daylot': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'paid': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'sent': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'stored': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"})
        },
        'sms.twakinzesubmission': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'TwakinzeSubmission', '_ormbases': ['sms.SMSSubmission']},
            'accountant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sms.Accountant']"}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'report_day': ('django.db.models.fields.DateField', [], {}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"}),
            'smssubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.SMSSubmission']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']"})
        },
        'sms.wetmillobserver': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'WetmillObserver', '_ormbases': ['sms.Actor']},
            'actor_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sms.Actor']", 'unique': 'True', 'primary_key': 'True'}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wetmills.Wetmill']", 'null': 'True', 'blank': 'True'})
        },
        'standards.standard': {
            'Meta': {'unique_together': "(('category', 'name'),)", 'object_name': 'Standard'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['standards.StandardCategory']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standard_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standard_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'})
        },
        'standards.standardcategory': {
            'Meta': {'object_name': 'StandardCategory'},
            'acronym': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standardcategory_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standardcategory_modifications'", 'to': "orm['auth.User']"}),
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
        'wetmills.wetmill': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('country', 'name'),)", 'object_name': 'Wetmill'},
            'altitude': ('django.db.models.fields.IntegerField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wetmill_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '20', 'decimal_places': '16', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '20', 'decimal_places': '16', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wetmill_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'province': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locales.Province']"}),
            'sms_name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'}),
            'sms_system': ('django.db.models.fields.CharField', [], {'default': "'FULL'", 'max_length': '4', 'null': 'True'}),
            'year_started': ('django.db.models.fields.IntegerField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sms']
