"""
Django signals for inspection app.

Signals:
- auto_create_car: Creates CAR when deficiency is saved (post_save)
- auto_clear_deficiency: Marks deficiency as cleared when action code 10 is set
"""

from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .deficiency_models import Deficiency, CAR


@receiver(post_save, sender=Deficiency)
def auto_create_car(sender, instance, created, **kwargs):
    """
    Auto-create CAR when a deficiency is created.

    Per BACKEND_STRUCTURE.md Section 8.1:
    - Every deficiency must have exactly one CAR (1:1 relationship)
    - CAR is created automatically, no manual creation allowed
    - CAR number format: PSC-{YEAR}-{SEQ}
    """
    if created and not instance.car:
        from apps.car.models import ActivityHistory

        # Generate CAR number
        car_number = CAR.generate_car_number()

        # Default CAR target date from deficiency target date or +7 days
        default_target_date = instance.target_date or (timezone.now().date() + timedelta(days=7))

        # Create CAR in ALLOTTED status
        car = CAR.objects.create(
            car_number=car_number,
            status='ALLOTTED',
            target_date=default_target_date,
            initial_action_code=instance.action_code,
            created_by=instance.created_by,
        )

        # Link CAR to deficiency
        instance.car = car
        # Use update to avoid triggering post_save again
        Deficiency.objects.filter(pk=instance.pk).update(car=car)

        # Record CAR creation activity for vessel timeline
        ActivityHistory.objects.create(
            entity_type='CAR',
            entity_id=car.id,
            vessel_id=instance.inspection.vessel_id,
            event_type='CAR_CREATED',
            event_description=f'CAR {car.car_number} created for deficiency {instance.def_code}',
            performed_by=instance.created_by or 'system',
            performed_by_name=instance.created_by or 'System',
        )


@receiver(post_save, sender=Deficiency)
def auto_clear_deficiency(sender, instance, **kwargs):
    """
    Auto-clear deficiency when action code 10 (Deficiency rectified) is set.

    Per BACKEND_STRUCTURE.md Section 8.2:
    - Action code 10 = "Deficiency rectified"
    - When set, is_cleared should be True and cleared_date should be set
    """
    # Action code 10 means "Deficiency rectified"
    RECTIFIED_CODE = 10

    if instance.action_code_id == RECTIFIED_CODE and not instance.is_cleared:
        Deficiency.objects.filter(pk=instance.pk).update(
            is_cleared=True,
            cleared_date=timezone.now().date()
        )
