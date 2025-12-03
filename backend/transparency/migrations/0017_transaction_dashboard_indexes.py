# Generated migration for dashboard performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transparency', '0016_dashboard_materialized_views'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['deleted', 'subject_committee', 'is_for_benefit'], name='idx_txn_dash_ie_benefit'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['transaction_type', 'deleted', 'entity', '-amount'], name='idx_txn_dash_donors'),
        ),
    ]
