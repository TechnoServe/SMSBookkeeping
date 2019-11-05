# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Report'
        db.create_table(u'sms_reports_report', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('day', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('hour', self.gf('django.db.models.fields.IntegerField')()),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('message_en_us', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('message_rw', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('message_ke_sw', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('message_tz_sw', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('message_am', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'sms_reports', ['Report'])

        # Adding M2M table for field reporter_types on 'Report'
        db.create_table(u'sms_reports_report_reporter_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('report', models.ForeignKey(orm[u'sms_reports.report'], null=False)),
            ('contenttype', models.ForeignKey(orm[u'contenttypes.contenttype'], null=False))
        ))
        db.create_unique(u'sms_reports_report_reporter_types', ['report_id', 'contenttype_id'])


    def backwards(self, orm):
        
        # Deleting model 'Report'
        db.delete_table(u'sms_reports_report')

        # Removing M2M table for field reporter_types on 'Report'
        db.delete_table('sms_reports_report_reporter_types')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'sms_reports.report': {
            'Meta': {'object_name': 'Report'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'day': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'hour': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'message_am': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'message_en_us': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'message_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'message_rw': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'message_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'reporter_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['contenttypes.ContentType']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['sms_reports']
