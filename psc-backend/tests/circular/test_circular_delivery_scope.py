import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from rest_framework.test import APIRequestFactory

from modules.circular.circular_office import views
from modules.circular.circular_ship import views as ship_views


class CircularDeliveryScopeTests(unittest.TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("modules.circular.circular_office.views.EmailMultiAlternatives")
    @patch("modules.circular.circular_office.views._bulk_insert_ship_delivery_records")
    @patch("modules.circular.circular_office.views._bulk_insert_crew_delivery_records")
    @patch("modules.circular.circular_office.views._fetch_target_crew_ids_for_vessels")
    @patch("modules.circular.circular_office.views._fetch_existing_ship_delivery_vessel_ids")
    @patch("modules.circular.circular_office.views._fetch_vessel_rows_by_ids")
    @patch("modules.circular.circular_office.views._get_latest_notification_record_by_sr_no")
    def test_vessel_delivery_creates_library_rows_even_when_email_is_missing(
        self,
        get_notification,
        fetch_vessels,
        fetch_existing,
        fetch_crews_for_vessels,
        insert_crew_records,
        insert_ship_records,
        email_class,
    ):
        vessel_with_email = "11111111-1111-1111-1111-111111111111"
        vessel_without_email = "22222222-2222-2222-2222-222222222222"
        notification_sr_no = "KSM/Circular/SEQ/2026-0001"

        get_notification.return_value = SimpleNamespace(
            id="99999999-9999-9999-9999-999999999999",
            sr_no=notification_sr_no,
            title="Safety circular",
        )
        fetch_vessels.return_value = {
            vessel_with_email: {
                "id": vessel_with_email,
                "vesselName": "Vessel A",
                "vesselCode": "VA",
                "email": "vessel-a@example.com",
            },
            vessel_without_email: {
                "id": vessel_without_email,
                "vesselName": "Vessel B",
                "vesselCode": "VB",
                "email": "",
            },
        }
        fetch_existing.return_value = set()
        insert_ship_records.return_value = [vessel_with_email, vessel_without_email]
        fetch_crews_for_vessels.return_value = ["KSM0005", "KSM0010"]
        insert_crew_records.return_value = ["KSM0005", "KSM0010"]
        email_message = MagicMock()
        email_class.return_value = email_message

        request = self.factory.post(
            "/api/circular/api/notifications/send-emails/",
            data={
                "notification_sr_no": notification_sr_no,
                "vessel_ids": [vessel_with_email, vessel_without_email],
            },
            format="json",
        )

        response = views.send_emails_to_vessels(request)
        payload = json.loads(response.content.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        insert_ship_records.assert_called_once()
        self.assertEqual(insert_ship_records.call_args.args[0], notification_sr_no)
        self.assertEqual(
            set(insert_ship_records.call_args.args[1]),
            {vessel_with_email, vessel_without_email},
        )
        fetch_crews_for_vessels.assert_called_once()
        self.assertEqual(
            set(fetch_crews_for_vessels.call_args.args[0]),
            {vessel_with_email, vessel_without_email},
        )
        insert_crew_records.assert_called_once()
        self.assertEqual(insert_crew_records.call_args.args[0], notification_sr_no)
        self.assertEqual(set(insert_crew_records.call_args.args[1]), {"KSM0005", "KSM0010"})
        email_message.send.assert_called_once()
        self.assertEqual(payload["delivery_records_created"], 2)
        self.assertEqual(payload["crew_delivery_records_created"], 2)
        self.assertEqual(payload["emails_sent"], 1)
        self.assertEqual(payload["vessels_without_email"], 1)

    @patch("modules.circular.circular_office.views.notify_circular_distribution")
    @patch("modules.circular.circular_office.views._bulk_insert_ship_delivery_records")
    @patch("modules.circular.circular_office.views._bulk_insert_rank_assignments")
    @patch("modules.circular.circular_office.views._bulk_insert_crew_delivery_records")
    @patch("modules.circular.circular_office.views._fetch_target_crew_ids_for_ranks")
    @patch("modules.circular.circular_office.views._get_latest_notification_record_by_sr_no")
    def test_rank_delivery_remains_personal_and_does_not_create_vessel_library_rows(
        self,
        get_notification,
        fetch_crews_for_ranks,
        insert_crew_records,
        insert_rank_assignments,
        insert_ship_records,
        notify_distribution,
    ):
        rank_id = "33333333-3333-3333-3333-333333333333"
        notification_sr_no = "KSM/Alert/SEQ/2026-0002"

        get_notification.return_value = SimpleNamespace(
            id="99999999-9999-9999-9999-999999999999",
            sr_no=notification_sr_no,
            title="Safety alert",
            msc_type_id=None,
        )
        fetch_crews_for_ranks.return_value = ["KSM0005", "KSM0010"]
        insert_crew_records.return_value = ["KSM0005", "KSM0010"]
        insert_rank_assignments.return_value = [rank_id]

        request = self.factory.post(
            f"/api/circular/api/notifications/{notification_sr_no}/link-ranks/",
            data={"selected_rank_ids": [rank_id]},
            format="json",
        )

        response = views.link_notification_to_ranks(request, notification_sr_no)
        payload = json.loads(response.content.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        fetch_crews_for_ranks.assert_called_once_with([rank_id])
        insert_crew_records.assert_called_once()
        insert_rank_assignments.assert_called_once()
        insert_ship_records.assert_not_called()
        notify_distribution.assert_called_once()
        self.assertEqual(payload["records_created"], 2)
        self.assertEqual(payload["rank_assignments_created"], 1)

    def test_master_rank_tokens_are_treated_as_vessel_library_users(self):
        self.assertTrue(ship_views._is_circular_master_role("MASTER"))
        self.assertTrue(ship_views._is_circular_master_role("MTR"))
        self.assertTrue(ship_views._is_circular_master_role("ACTING MASTER"))

    @patch("modules.circular.circular_ship.views.get_master_notifications")
    @patch("modules.circular.circular_ship.views.connection")
    def test_master_rank_hitting_crew_endpoint_uses_vessel_library_delivery(
        self,
        connection_mock,
        get_master_notifications,
    ):
        hrm_cursor = MagicMock()
        hrm_cursor.__enter__.return_value = hrm_cursor
        hrm_cursor.fetchone.return_value = (
            "crew-row-id",
            "auto-id",
            "user-id",
            "8cb48654-4688-ee11-987b-745d223e029b",
        )

        rank_cursor = MagicMock()
        rank_cursor.__enter__.return_value = rank_cursor
        rank_cursor.fetchone.return_value = ("MASTER", "MTR")

        connection_mock.cursor.side_effect = [hrm_cursor, rank_cursor]
        get_master_notifications.return_value = views.JsonResponse(
            [{"sr_no": "KSM/Circular/SEQ/2026-0006"}],
            safe=False,
        )

        request = self.factory.get(
            "/api/circular/api/crew/notifications/",
            {"crew_id": "KSM0006"},
        )

        response = ship_views.get_non_master_notifications(request)
        payload = json.loads(response.content.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload[0]["sr_no"], "KSM/Circular/SEQ/2026-0006")
        get_master_notifications.assert_called_once()
