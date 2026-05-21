from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django


bootstrap_django()

from apps.safety.models import SCMMeeting


class SCMModelTests(unittest.TestCase):
    def test_meeting_uses_expected_table_and_defaults(self) -> None:
        meeting = SCMMeeting(
            vessel_id="7",
            scm_number="ABC-28-Apr-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date="2026-04-28",
            meeting_time_local="10:00:00",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            created_by="co-7",
        )

        self.assertEqual(meeting._meta.db_table, "vims_safety_scm_meeting")
        self.assertEqual(meeting.state, SCMMeeting.State.DRAFT)
        self.assertEqual(meeting.schema_version, 1)
        self.assertEqual(
            [choice for choice, _label in SCMMeeting.MeetingType.choices],
            ["REGULAR", "AD_HOC"],
        )

