from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_scm_tables


bootstrap_django()

from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SCMMeeting
from apps.safety.views.scm import SCMCreateRegularView


def build_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="co-7",
        username="co-7",
        role_name="CO",
        form_ids=["SAF_F_003"],
        process_ids=["SAF_P_001"],
        vessel_ids=["7"],
        is_global=False,
    )


class SCMCadenceWarningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        self.factory = APIRequestFactory()
        self.view = SCMCreateRegularView.as_view()

    def test_regular_create_config_warns_when_last_regular_closure_is_older_than_30_days(self) -> None:
        closure_date = timezone.localdate() - timedelta(days=40)
        SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-01-Mar-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=closure_date,
            meeting_time_local=datetime.strptime("09:00:00", "%H:%M:%S").time(),
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.SIGNED_OFF,
            master_signed_off_at=timezone.make_aware(datetime.combine(closure_date, datetime.min.time())),
            master_signed_off_by="master-7",
            created_by="co-7",
        )

        request = self.factory.get("/api/safety/scm/create-regular/?vessel_id=7")
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meeting_type"], "REGULAR")
        self.assertEqual(response.data["cadence_warning"]["severity"], "warning")
        self.assertGreaterEqual(response.data["cadence_warning"]["days_since_last_regular_closure"], 40)

    def test_cadence_anchor_uses_latest_signed_off_scm_even_when_adhoc_is_latest(self) -> None:
        old_regular_date = timezone.localdate() - timedelta(days=45)
        latest_adhoc_date = timezone.localdate() - timedelta(days=10)
        SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-OLD-REGULAR",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=old_regular_date,
            meeting_time_local=datetime.strptime("09:00:00", "%H:%M:%S").time(),
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.SIGNED_OFF,
            master_signed_off_at=timezone.make_aware(datetime.combine(old_regular_date, datetime.min.time())),
            master_signed_off_by="master-7",
            created_by="co-7",
        )
        SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-LATEST-ADHOC",
            meeting_type=SCMMeeting.MeetingType.AD_HOC,
            meeting_date=latest_adhoc_date,
            meeting_time_local=datetime.strptime("10:00:00", "%H:%M:%S").time(),
            chair_crew_id="master-7",
            prepared_by_crew_id="master-7",
            ad_hoc_trigger_reason="Urgent safety review",
            state=SCMMeeting.State.SIGNED_OFF,
            master_signed_off_at=timezone.make_aware(datetime.combine(latest_adhoc_date, datetime.min.time())),
            master_signed_off_by="master-7",
            created_by="master-7",
        )

        request = self.factory.get("/api/safety/scm/create-regular/?vessel_id=7")
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["cadence_warning"])
        self.assertEqual(response.data["cadence_status"]["last_scm_type"], SCMMeeting.MeetingType.AD_HOC)
