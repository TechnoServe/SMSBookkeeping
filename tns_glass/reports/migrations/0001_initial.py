# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Report'
        db.create_table('reports_report', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='report_creations', to=orm['auth.User'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='report_modifications', to=orm['auth.User'])),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('season', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reports', to=orm['seasons.Season'])),
            ('wetmill', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reports', to=orm['wetmills.Wetmill'])),
            ('working_capital', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2, blank=True)),
            ('working_capital_repaid', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2, blank=True)),
            ('miscellaneous_sources', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2, blank=True)),
            ('miscellaneous_revenue', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2, blank=True)),
            ('cherry_production_by_members', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2, blank=True)),
            ('capacity', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2, blank=True)),
            ('is_finalized', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('farmer_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=4, blank=True)),
            ('farmer_share', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=4, blank=True)),
            ('production_cost', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=4, blank=True)),
            ('cherry_to_green_ratio', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=4, blank=True)),
        ))
        db.send_create_signal('reports', ['Report'])

        # Adding unique constraint on 'Report', fields ['season', 'wetmill']
        db.create_unique('reports_report', ['season_id', 'wetmill_id'])

        # Adding model 'Production'
        db.create_table('reports_production', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='production_creations', to=orm['auth.User'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='production_modifications', to=orm['auth.User'])),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(related_name='production', to=orm['reports.Report'])),
            ('grade', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['grades.Grade'])),
            ('volume', self.gf('django.db.models.fields.DecimalField')(max_digits=16, decimal_places=2)),
        ))
        db.send_create_signal('reports', ['Production'])

        # Adding unique constraint on 'Production', fields ['report', 'grade']
        db.create_unique('reports_production', ['report_id', 'grade_id'])

        # Adding model 'CashUseEntry'
        db.create_table('reports_cashuseentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cashuseentry_creations', to=orm['auth.User'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cashuseentry_modifications', to=orm['auth.User'])),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cashuses', to=orm['reports.Report'])),
            ('cashuse', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cashuses.CashUse'])),
            ('total', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2)),
            ('all_per_kilo', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2)),
            ('member_per_kilo', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2)),
            ('non_member_per_kilo', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2)),
        ))
        db.send_create_signal('reports', ['CashUseEntry'])

        # Adding unique constraint on 'CashUseEntry', fields ['report', 'cashuse']
        db.create_unique('reports_cashuseentry', ['report_id', 'cashuse_id'])

        # Adding model 'ExpenseEntry'
        db.create_table('reports_expenseentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='expenseentry_creations', to=orm['auth.User'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='expenseentry_modifications', to=orm['auth.User'])),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(related_name='expenses', to=orm['reports.Report'])),
            ('expense', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['expenses.Expense'])),
            ('value', self.gf('django.db.models.fields.DecimalField')(max_digits=16, decimal_places=2)),
            ('exchange_rate', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('reports', ['ExpenseEntry'])

        # Adding unique constraint on 'ExpenseEntry', fields ['report', 'expense']
        db.create_unique('reports_expenseentry', ['report_id', 'expense_id'])

        # Adding model 'Sale'
        db.create_table('reports_sale', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sale_creations', to=orm['auth.User'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sale_modifications', to=orm['auth.User'])),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sales', to=orm['reports.Report'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('buyer', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('currency', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locales.Currency'])),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=16, decimal_places=4)),
            ('exchange_rate', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2, blank=True)),
            ('sale_type', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('adjustment', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=16, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('reports', ['Sale'])

        # Adding model 'SaleComponent'
        db.create_table('reports_salecomponent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='salecomponent_creations', to=orm['auth.User'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='salecomponent_modifications', to=orm['auth.User'])),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('sale', self.gf('django.db.models.fields.related.ForeignKey')(related_name='components', to=orm['reports.Sale'])),
            ('grade', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sale_components', to=orm['grades.Grade'])),
            ('volume', self.gf('django.db.models.fields.DecimalField')(max_digits=16, decimal_places=2)),
        ))
        db.send_create_signal('reports', ['SaleComponent'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'ExpenseEntry', fields ['report', 'expense']
        db.delete_unique('reports_expenseentry', ['report_id', 'expense_id'])

        # Removing unique constraint on 'CashUseEntry', fields ['report', 'cashuse']
        db.delete_unique('reports_cashuseentry', ['report_id', 'cashuse_id'])

        # Removing unique constraint on 'Production', fields ['report', 'grade']
        db.delete_unique('reports_production', ['report_id', 'grade_id'])

        # Removing unique constraint on 'Report', fields ['season', 'wetmill']
        db.delete_unique('reports_report', ['season_id', 'wetmill_id'])

        # Deleting model 'Report'
        db.delete_table('reports_report')

        # Deleting model 'Production'
        db.delete_table('reports_production')

        # Deleting model 'CashUseEntry'
        db.delete_table('reports_cashuseentry')

        # Deleting model 'ExpenseEntry'
        db.delete_table('reports_expenseentry')

        # Deleting model 'Sale'
        db.delete_table('reports_sale')

        # Deleting model 'SaleComponent'
        db.delete_table('reports_salecomponent')


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
        'cashuses.cashuse': {
            'Meta': {'object_name': 'CashUse'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cashuse_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cashuse_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
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
        'reports.cashuseentry': {
            'Meta': {'ordering': "('cashuse__order', 'cashuse__name')", 'unique_together': "(('report', 'cashuse'),)", 'object_name': 'CashUseEntry'},
            'all_per_kilo': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2'}),
            'cashuse': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cashuses.CashUse']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cashuseentry_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'member_per_kilo': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cashuseentry_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'non_member_per_kilo': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cashuses'", 'to': "orm['reports.Report']"}),
            'total': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2'})
        },
        'reports.expenseentry': {
            'Meta': {'ordering': "('expense__name',)", 'unique_together': "(('report', 'expense'),)", 'object_name': 'ExpenseEntry'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'expenseentry_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'exchange_rate': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2', 'blank': 'True'}),
            'expense': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['expenses.Expense']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'expenseentry_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'expenses'", 'to': "orm['reports.Report']"}),
            'value': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'})
        },
        'reports.production': {
            'Meta': {'ordering': "('grade__order', 'grade__name')", 'unique_together': "(('report', 'grade'),)", 'object_name': 'Production'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'production_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'grade': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['grades.Grade']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'production_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'production'", 'to': "orm['reports.Report']"}),
            'volume': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'})
        },
        'reports.report': {
            'Meta': {'unique_together': "(('season', 'wetmill'),)", 'object_name': 'Report'},
            'capacity': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2', 'blank': 'True'}),
            'cherry_production_by_members': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2', 'blank': 'True'}),
            'cherry_to_green_ratio': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '4', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'report_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'farmer_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '4', 'blank': 'True'}),
            'farmer_share': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '4', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_finalized': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'miscellaneous_revenue': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2', 'blank': 'True'}),
            'miscellaneous_sources': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'report_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'production_cost': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '4', 'blank': 'True'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': "orm['seasons.Season']"}),
            'wetmill': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': "orm['wetmills.Wetmill']"}),
            'working_capital': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2', 'blank': 'True'}),
            'working_capital_repaid': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2', 'blank': 'True'})
        },
        'reports.sale': {
            'Meta': {'ordering': "('date',)", 'object_name': 'Sale'},
            'adjustment': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2', 'blank': 'True'}),
            'buyer': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sale_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locales.Currency']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'exchange_rate': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '16', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sale_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '4'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sales'", 'to': "orm['reports.Report']"}),
            'sale_type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        'reports.salecomponent': {
            'Meta': {'ordering': "('grade__name',)", 'object_name': 'SaleComponent'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'salecomponent_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'grade': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sale_components'", 'to': "orm['grades.Grade']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'salecomponent_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sale': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'components'", 'to': "orm['reports.Sale']"}),
            'volume': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'})
        },
        'seasons.season': {
            'Meta': {'ordering': "('country__name', '-name')", 'unique_together': "(('country', 'name'),)", 'object_name': 'Season'},
            'cashuses': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cashuses.CashUse']", 'through': "orm['seasons.SeasonCashUse']", 'symmetrical': 'False'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'season_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_adjustment': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'exchange_rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
            'expenses': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['expenses.Expense']", 'through': "orm['seasons.SeasonExpense']", 'symmetrical': 'False'}),
            'farmer_income_baseline': ('django.db.models.fields.DecimalField', [], {'max_digits': '16', 'decimal_places': '2'}),
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
            'standards': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['standards.Standard']", 'symmetrical': 'False'})
        },
        'seasons.seasoncashuse': {
            'Meta': {'ordering': "('cashuse__order',)", 'unique_together': "(('season', 'cashuse'),)", 'object_name': 'SeasonCashUse'},
            'applies_to': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'cashuse': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cashuses.CashUse']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seasons.Season']"})
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
        'standards.standard': {
            'Meta': {'object_name': 'Standard'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['standards.StandardCategory']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standard_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standard_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name_am': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_en_us': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_ke_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_rw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name_tz_sw': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
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
            'order': ('django.db.models.fields.IntegerField', [], {'max_length': '2'})
        },
        'wetmills.wetmill': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('country', 'name'),)", 'object_name': 'Wetmill'},
            'altitude': ('django.db.models.fields.IntegerField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locales.Country']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wetmill_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'farmers': ('django.db.models.fields.IntegerField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
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

    complete_apps = ['reports']
