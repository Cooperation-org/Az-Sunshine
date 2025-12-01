# backend/transparency/migrations/0002_add_email_tracking.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transparency', '0001_initial'),
    ]

    operations = [
        # Add tracking_id to EmailLog
        migrations.AddField(
            model_name='emaillog',
            name='tracking_id',
            field=models.CharField(max_length=64, unique=True, null=True, blank=True, db_index=True),
        ),
        
        # Add source_url to CandidateStatementOfInterest if not exists
        migrations.AddField(
            model_name='candidatestatementofinterest',
            name='source_url',
            field=models.URLField(max_length=500, null=True, blank=True, db_index=True),
        ),
        
        # Add phone field if not exists
        migrations.AddField(
            model_name='candidatestatementofinterest',
            name='phone',
            field=models.CharField(max_length=100, blank=True, db_index=True),
        ),
    ]


# Run migration:
# python manage.py makemigrations
# python manage.py migrate