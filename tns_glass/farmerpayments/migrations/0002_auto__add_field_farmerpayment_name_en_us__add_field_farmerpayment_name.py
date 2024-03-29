# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'FarmerPayment.name_en_us'
        db.add_column('farmerpayments_farmerpayment', 'name_en_us', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True, null=True, blank=True), keep_default=False)

        # Adding field 'FarmerPayment.name_rw'
        db.add_column('farmerpayments_farmerpayment', 'name_rw', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True, null=True, blank=True), keep_default=False)

        # Adding field 'FarmerPayment.name_ke_sw'
        db.add_column('farmerpayments_farmerpayment', 'name_ke_sw', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True, null=True, blank=True), keep_default=False)

        # Adding field 'FarmerPayment.name_tz_sw'
        db.add_column('farmerpayments_farmerpayment', 'name_tz_sw', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True, null=True, blank=True), keep_default=False)

        # Adding field 'FarmerPayment.name_am'
        db.add_column('farmerpayments_farmerpayment', 'name_am', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'FarmerPayment.name_en_us'
        db.delete_column('farmerpayments_farmerpayment', 'name_en_us')

        # Deleting field 'FarmerPayment.name_rw'
        db.delete_column('farmerpayments_farmerpayment', 'name_rw')

        # Deleting field 'FarmerPayment.name_ke_sw'
        db.delete_column('farmerpayments_farmerpayment', 'name_ke_sw')

        # Deleting field 'FarmerPayment.name_tz_sw'
        db.delete_column('farmerpayments_farmerpayment', 'name_tz_sw')

        # Deleting field 'FarmerPayment.name_am'
        db.delete_column('farmerpayments_farmerpayment', 'name_am')


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'farmerpayments.farmerpayment': {
            'Meta': {'ordering': "('order',)", 'object_name': 'FarmerPayment'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'farmerpayment_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'farmerpayment_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['farmerpayments']
