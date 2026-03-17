"""
Management command to check for overdue corrective actions and send notifications.

Usage:
    python manage.py check_overdue_actions

Implements: PRD.md FEAT-NOTIF-001
- ACTION_OVERDUE_WARNING (T-3 days) → Action Owner + Master
- ACTION_OVERDUE (past due) → Action Owner + Master + Office

This command should be run daily via cron or task scheduler:
    0 8 * * * cd /path/to/psc-backend && python manage.py check_overdue_actions
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.car.models import CorrectiveAction
from apps.inspection.deficiency_models import CARStatus
from apps.notifications.models import Notification, NotificationType, RecipientType
from apps.notifications.signals import (
    create_notification,
    _get_vessel_master_crew_ids,
    _get_office_users_for_vessel,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for overdue corrective actions and send notifications.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        warning_date = today + timedelta(days=3)

        self.stdout.write(f'Checking overdue actions as of {today}...')

        # Get all open (not completed, not deleted) corrective actions with due dates
        open_actions = CorrectiveAction.objects.filter(
            is_completed=False,
            is_deleted=False,
            due_date__isnull=False,
            car__is_deleted=False,
            car__status__in=[CARStatus.DRAFT, CARStatus.SUBMITTED, CARStatus.PIC_ACCEPTED],
        ).select_related('car', 'car__deficiency', 'car__deficiency__inspection')

        warning_count = 0
        overdue_count = 0

        for action in open_actions:
            car = action.car
            vessel_id = self._get_vessel_id(action)
            if not vessel_id:
                continue

            # Check if already notified today for this action
            if action.due_date == warning_date:
                # T-3 days warning
                if not self._already_notified_today(
                    NotificationType.ACTION_OVERDUE_WARNING,
                    str(action.id),
                    today,
                ):
                    self._send_warning_notification(action, car, vessel_id)
                    warning_count += 1

            elif action.due_date < today:
                # Past due
                if not self._already_notified_today(
                    NotificationType.ACTION_OVERDUE,
                    str(action.id),
                    today,
                ):
                    self._send_overdue_notification(action, car, vessel_id)
                    overdue_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Warnings sent: {warning_count}, Overdue sent: {overdue_count}'
        ))

    def _get_vessel_id(self, action) -> str | None:
        """Get vessel_id from action → CAR → deficiency → inspection."""
        try:
            return str(action.car.deficiency.inspection.vessel_id)
        except (AttributeError, Exception):
            return None

    def _already_notified_today(self, notification_type: str, entity_id: str, today) -> bool:
        """Check if a notification of this type was already sent today for this entity."""
        return Notification.objects.filter(
            notification_type=notification_type,
            entity_id=entity_id,
            created_date__date=today,
        ).exists()

    def _send_warning_notification(self, action, car, vessel_id: str):
        """
        ACTION_OVERDUE_WARNING → Action Owner + Master.

        Sent T-3 days before action due date.
        """
        days_label = f'due in 3 days ({action.due_date})'
        recipients = self._get_action_owner_and_masters(action, vessel_id)

        for rtype, rid in recipients:
            create_notification(
                recipient_type=rtype,
                recipient_id=rid,
                notification_type=NotificationType.ACTION_OVERDUE_WARNING,
                title=f'Action due soon: {car.car_number}',
                message=f'Corrective action "{action.description[:80]}" is {days_label}.',
                vessel_id=vessel_id,
                entity_type='ACTION',
                entity_id=str(action.id),
            )

    def _send_overdue_notification(self, action, car, vessel_id: str):
        """
        ACTION_OVERDUE → Action Owner + Master + Office.

        Sent when action is past due.
        """
        days_overdue = (timezone.now().date() - action.due_date).days
        recipients = self._get_action_owner_and_masters(action, vessel_id)

        # Also notify office users for overdue (not just warning)
        office_ids = _get_office_users_for_vessel(vessel_id)
        for eid in office_ids:
            recipients.add((RecipientType.OFFICE, eid))

        for rtype, rid in recipients:
            create_notification(
                recipient_type=rtype,
                recipient_id=rid,
                notification_type=NotificationType.ACTION_OVERDUE,
                title=f'Action overdue: {car.car_number}',
                message=f'Corrective action "{action.description[:80]}" is {days_overdue} day(s) overdue.',
                vessel_id=vessel_id,
                entity_type='ACTION',
                entity_id=str(action.id),
            )

    def _get_action_owner_and_masters(self, action, vessel_id: str) -> set[tuple[RecipientType, str]]:
        """Get recipients: action owner + vessel masters."""
        recipients = set()

        # Vessel masters
        master_ids = _get_vessel_master_crew_ids(vessel_id)
        for crew_id in master_ids:
            recipients.add((RecipientType.CREW, crew_id))

        # Action owner (crew member)
        if action.owner_crew_id:
            from apps.accounts.models import HRM501
            crew = HRM501.objects.filter(
                id=action.owner_crew_id,
                is_active=True,
                is_deleted=False,
            ).first()
            if crew:
                recipients.add((RecipientType.CREW, crew.CrewID))

        return recipients
