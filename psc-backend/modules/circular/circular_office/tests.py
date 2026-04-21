from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from .views import (
    _build_delivery_status_records,
    _build_pending_draft_conflict_message,
    _get_existing_active_draft_for_creator_and_type,
    _generate_unique_circular_sr_no,
    delete_draft_by_id,
)


class DeliveryStatusRecordTests(SimpleTestCase):
    @patch('modules.circular.circular_office.views.connection')
    def test_build_delivery_status_records_dedupes_and_sorts_by_rank_level(self, mock_connection):
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [
            ('CREW-1', 'John', 'Master', 'Master', 1, 'Vessel A', 'On Board'),
            ('CREW-2', 'Amy', 'Engineer', 'Chief Engineer', 2, 'Vessel B', 'Retired'),
        ]

        records = [
            SimpleNamespace(
                crew_id='CREW-2',
                seen_at=None,
                reminder_sent_at=datetime(2026, 4, 19, 9, 0, 0),
            ),
            SimpleNamespace(
                crew_id='CREW-1',
                seen_at=datetime(2026, 4, 20, 8, 30, 0),
                reminder_sent_at=None,
            ),
            SimpleNamespace(
                crew_id='CREW-2',
                seen_at=datetime(2026, 4, 20, 7, 0, 0),
                reminder_sent_at=datetime(2026, 4, 20, 6, 0, 0),
            ),
        ]

        result = _build_delivery_status_records(records)

        self.assertEqual([row['resolved_crew_id'] for row in result], ['CREW-1', 'CREW-2'])
        self.assertEqual(result[1]['crew_name'], 'Amy Engineer')
        self.assertEqual(result[1]['rank_name'], 'Chief Engineer')
        self.assertEqual(result[1]['crew_status_name'], 'Retired')
        self.assertEqual(result[1]['seen_at'], '2026-04-20T07:00:00')
        self.assertEqual(result[1]['reminder_sent_at'], '2026-04-20T06:00:00')


class DeleteDraftByIdTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch('modules.circular.circular_office.views.connection')
    def test_delete_draft_by_id_soft_deletes_with_try_convert_uuid(self, mock_connection):
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.rowcount = 1
        draft_id = '4f9d4c5d-4ff9-4bb2-ace5-f346785a38f7'

        response = delete_draft_by_id(
            self.factory.post(f'/api/circular/api/drafts/{draft_id}/delete/'),
            draft_id,
        )

        self.assertEqual(response.status_code, 200)
        mock_cursor.execute.assert_called_once()
        executed_sql, executed_params = mock_cursor.execute.call_args[0]
        self.assertIn('TRY_CONVERT(uniqueidentifier, %s)', executed_sql)
        self.assertEqual(executed_params, [draft_id])

    def test_delete_draft_by_id_rejects_invalid_uuid(self):
        response = delete_draft_by_id(
            self.factory.post('/api/circular/api/drafts/not-a-uuid/delete/'),
            'not-a-uuid',
        )

        self.assertEqual(response.status_code, 400)


class CircularSrNumberTests(SimpleTestCase):
    @patch('modules.circular.circular_office.views._acquire_circular_sr_lock')
    def test_generate_unique_circular_sr_no_ignores_deleted_drafts_and_rejected_records(self, mock_lock):
        class CursorStub:
            def __init__(self):
                self.calls = []
                self._fetchone_values = [(4,), (0,)]

            def execute(self, sql, params):
                self.calls.append((sql, params))

            def fetchone(self):
                return self._fetchone_values.pop(0)

        cursor = CursorStub()

        result = _generate_unique_circular_sr_no(
            cursor,
            'Alert',
            'Technical',
            datetime(2026, 4, 21, 10, 0, 0),
        )

        self.assertEqual(result, 'KSM/Alert/Technical/2026-0005')
        self.assertEqual(len(cursor.calls), 2)
        self.assertIn('publish_status = 0', cursor.calls[0][0])
        self.assertIn('ISNULL(is_deleted, 0) = 1', cursor.calls[0][0])
        self.assertIn('publish_status = 3', cursor.calls[0][0])
        self.assertIn('publish_status = 0', cursor.calls[1][0])
        self.assertIn('ISNULL(is_deleted, 0) = 1', cursor.calls[1][0])
        self.assertIn('publish_status = 3', cursor.calls[1][0])


class PendingDraftValidationTests(SimpleTestCase):
    def test_build_pending_draft_conflict_message_uses_expected_copy(self):
        self.assertEqual(
            _build_pending_draft_conflict_message('WorkInstruction'),
            'There is already a draft pending for Work Instruction. Please clear that first to avoid sequence disturbance.',
        )

    @patch('modules.circular.circular_office.views.connection')
    def test_get_existing_active_draft_for_creator_and_type_filters_same_user_type_and_active(self, mock_connection):
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = (
            'draft-1',
            'KSM/Work Instruction/Technical/2026-0001',
        )

        result = _get_existing_active_draft_for_creator_and_type(
            ' EMP001 ',
            '4f9d4c5d-4ff9-4bb2-ace5-f346785a38f7',
            'Work Instruction',
        )

        self.assertEqual(result.id, 'draft-1')
        self.assertEqual(result.sr_no, 'KSM/Work Instruction/Technical/2026-0001')
        mock_cursor.execute.assert_called_once()
        executed_sql, executed_params = mock_cursor.execute.call_args[0]
        self.assertIn('TRY_CONVERT(uniqueidentifier, msc_type)', executed_sql)
        self.assertIn("REPLACE(LOWER(LTRIM(RTRIM(CONVERT(NVARCHAR(255), msc_type)))), ' ', '') = %s", executed_sql)
        self.assertEqual(
            executed_params,
            [
                'EMP001',
                '4f9d4c5d-4ff9-4bb2-ace5-f346785a38f7',
                '4f9d4c5d-4ff9-4bb2-ace5-f346785a38f7',
                'workinstruction',
                'workinstruction',
            ],
        )
