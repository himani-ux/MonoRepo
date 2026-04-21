from datetime import datetime
from types import SimpleNamespace

from django.test import SimpleTestCase

from .views import _is_circular_master_role, _select_ack_notification_record


class CircularShipAcknowledgeHelpersTests(SimpleTestCase):
    def test_is_circular_master_role_accepts_vessel_master(self):
        self.assertTrue(_is_circular_master_role('VESSEL_MASTER'))
        self.assertTrue(_is_circular_master_role('MASTER'))
        self.assertFalse(_is_circular_master_role('VESSEL_CREW'))

    def test_select_ack_notification_record_prefers_highest_reminder_and_latest_dates(self):
        older = SimpleNamespace(
            reminder_count=1,
            reminder_sent_at=datetime(2026, 4, 19, 8, 0, 0),
            delivered_at=datetime(2026, 4, 18, 8, 0, 0),
            seen_at=None,
        )
        newer = SimpleNamespace(
            reminder_count=4,
            reminder_sent_at=datetime(2026, 4, 20, 8, 0, 0),
            delivered_at=datetime(2026, 4, 20, 7, 0, 0),
            seen_at=None,
        )

        selected = _select_ack_notification_record([older, newer])

        self.assertIs(selected, newer)

    def test_select_ack_notification_record_returns_none_for_empty_input(self):
        self.assertIsNone(_select_ack_notification_record([]))
