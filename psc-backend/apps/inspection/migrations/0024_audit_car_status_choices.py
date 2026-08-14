# Generated manually for VIMS Audit Phase 3 Step 3.3 on 2026-07-29.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inspection", "0023_audit_seed_text_widths"),
    ]

    operations = [
        migrations.AlterField(
            model_name="car",
            name="status",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"),
                    ("ALLOTTED", "Allotted"),
                    ("IN_PROGRESS", "In Progress"),
                    ("OFFICE_DRAFTED", "Office Drafted"),
                    ("PENDING_CE_REVIEW", "Pending CE Review"),
                    ("PENDING_MASTER_REVIEW", "Pending Master Review"),
                    ("SUBMITTED_TO_PIC", "Submitted to PIC"),
                    ("PIC_REVIEW", "PIC Review"),
                    ("SUBMITTED_TO_LEAD_AUDITOR", "Submitted to Lead Auditor"),
                    ("LEAD_AUDITOR_CLOSED", "Lead Auditor Closed"),
                    ("AWAITING_EXTERNAL_CLOSE_OUT", "Awaiting External Close Out"),
                    ("EXTERNAL_AUDITOR_CLOSED", "External Auditor Closed"),
                    ("SUBMITTED_TO_DPA", "Submitted to DPA"),
                    ("CLOSED", "Closed"),
                    ("RETURNED_FOR_REWORK", "Returned for Rework"),
                ],
                db_index=True,
                default="ALLOTTED",
                max_length=30,
            ),
        ),
    ]

