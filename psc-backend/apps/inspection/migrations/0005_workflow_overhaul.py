"""
Migration: Workflow overhaul — unified CAR status.

Replaces 5-value CARStatus with 9-value unified workflow status.
Adds verification_pending, last_action* fields to CAR.
Maps old status values to new ones.
"""

from django.db import migrations, models


def migrate_statuses_forward(apps, schema_editor):
    """Map old CARStatus values to new ones."""
    CAR = apps.get_model('inspection', 'CAR')
    mapping = {
        'DRAFT': 'ALLOTTED',
        'SUBMITTED': 'SUBMITTED_TO_PIC',
        'PIC_ACCEPTED': 'PIC_REVIEW',
        'REWORK_REQUESTED': 'PENDING_MASTER_REVIEW',
        'DPA_CLOSED': 'CLOSED',
    }
    for old_val, new_val in mapping.items():
        CAR.objects.filter(status=old_val).update(status=new_val)


def migrate_statuses_reverse(apps, schema_editor):
    """Map new CARStatus values back to old ones."""
    CAR = apps.get_model('inspection', 'CAR')
    mapping = {
        'ALLOTTED': 'DRAFT',
        'IN_PROGRESS': 'DRAFT',
        'PENDING_CE_REVIEW': 'DRAFT',
        'PENDING_MASTER_REVIEW': 'REWORK_REQUESTED',
        'SUBMITTED_TO_PIC': 'SUBMITTED',
        'PIC_REVIEW': 'PIC_ACCEPTED',
        'SUBMITTED_TO_DPA': 'PIC_ACCEPTED',
        'CLOSED': 'DPA_CLOSED',
        'RETURNED_FOR_REWORK': 'REWORK_REQUESTED',
    }
    for new_val, old_val in mapping.items():
        CAR.objects.filter(status=new_val).update(status=old_val)


class Migration(migrations.Migration):

    dependencies = [
        ('inspection', '0004_add_deficiency_workflow_fields'),
    ]

    operations = [
        # Add new fields first (before data migration)
        migrations.AddField(
            model_name='car',
            name='verification_pending',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='car',
            name='last_action',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='car',
            name='last_action_by',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='car',
            name='last_action_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='car',
            name='last_action_comment',
            field=models.TextField(blank=True, null=True),
        ),
        # Data migration: map old statuses to new
        migrations.RunPython(migrate_statuses_forward, migrate_statuses_reverse),
        # Alter the status field choices and default
        migrations.AlterField(
            model_name='car',
            name='status',
            field=models.CharField(
                choices=[
                    ('ALLOTTED', 'Allotted'),
                    ('IN_PROGRESS', 'In Progress'),
                    ('PENDING_CE_REVIEW', 'Pending CE Review'),
                    ('PENDING_MASTER_REVIEW', 'Pending Master Review'),
                    ('SUBMITTED_TO_PIC', 'Submitted to PIC'),
                    ('PIC_REVIEW', 'PIC Review'),
                    ('SUBMITTED_TO_DPA', 'Submitted to DPA'),
                    ('CLOSED', 'Closed'),
                    ('RETURNED_FOR_REWORK', 'Returned for Rework'),
                ],
                db_index=True,
                default='ALLOTTED',
                max_length=30,
            ),
        ),
    ]
