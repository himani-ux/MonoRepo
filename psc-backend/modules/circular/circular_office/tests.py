import io
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.utils.datastructures import MultiValueDict
from rest_framework.test import APIRequestFactory
from PyPDF2.errors import DependencyError

from .views import (
    MAX_CIRCULAR_ATTACHMENT_FILES,
    CircularAttachmentValidationError,
    _build_delivery_status_records,
    _extract_uploaded_pdf_attachments_from_request_files,
    _get_latest_notification_record_by_sr_no,
    _build_pending_draft_conflict_message,
    _get_existing_active_draft_for_creator_and_type,
    _generate_unique_circular_sr_no,
    _open_uploaded_pdf_reader,
    create_delivery_records,
    delete_draft_by_id,
    get_notification_details_by_sr_no,
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
        mock_lock.assert_called_once_with(cursor, 'type-seq:alert')
        self.assertEqual(cursor.calls[0][1], ['KSM/Alert/', 'KSM/Alert/'])
        self.assertEqual(cursor.calls[1][1], ['KSM/Alert/', 'KSM/Alert/', 5])
        self.assertIn('publish_status = 0', cursor.calls[0][0])
        self.assertIn('ISNULL(is_deleted, 0) = 1', cursor.calls[0][0])
        self.assertIn('publish_status = 3', cursor.calls[0][0])
        self.assertIn('publish_status = 0', cursor.calls[1][0])
        self.assertIn('ISNULL(is_deleted, 0) = 1', cursor.calls[1][0])
        self.assertIn('publish_status = 3', cursor.calls[1][0])

    @patch('modules.circular.circular_office.views._acquire_circular_sr_lock')
    def test_generate_unique_circular_sr_no_continues_across_department_and_year(self, mock_lock):
        class CursorStub:
            def __init__(self):
                self.calls = []
                self._fetchone_values = [(129,), (0,)]

            def execute(self, sql, params):
                self.calls.append((sql, params))

            def fetchone(self):
                return self._fetchone_values.pop(0)

        cursor = CursorStub()

        result = _generate_unique_circular_sr_no(
            cursor,
            'Alert',
            'SEQ',
            datetime(2027, 1, 5, 10, 0, 0),
        )

        self.assertEqual(result, 'KSM/Alert/SEQ/2027-0130')
        mock_lock.assert_called_once_with(cursor, 'type-seq:alert')
        self.assertEqual(cursor.calls[0][1], ['KSM/Alert/', 'KSM/Alert/'])
        self.assertEqual(cursor.calls[1][1], ['KSM/Alert/', 'KSM/Alert/', 130])


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


class NotificationLookupTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch('modules.circular.circular_office.views.MscData.objects')
    def test_get_latest_notification_record_by_sr_no_uses_first_instead_of_get(self, mock_objects):
        expected_record = SimpleNamespace(id='note-1', sr_no='KSM/Circular/Technical/2026-0001')
        mock_ordered_queryset = mock_objects.filter.return_value.order_by.return_value
        mock_ordered_queryset.first.return_value = expected_record
        mock_ordered_queryset.count.return_value = 2

        result = _get_latest_notification_record_by_sr_no(' KSM/Circular/Technical/2026-0001 ')

        self.assertIs(result, expected_record)
        mock_objects.filter.assert_called_once_with(
            sr_no='KSM/Circular/Technical/2026-0001',
            is_deleted=False,
        )
        mock_objects.get.assert_not_called()

    @patch('modules.circular.circular_office.views._get_latest_notification_record_by_sr_no')
    def test_get_notification_details_by_sr_no_uses_latest_helper(self, mock_lookup):
        mock_lookup.return_value = SimpleNamespace(
            id='note-1',
            sr_no='KSM/Circular/Technical/2026-0001',
            title='Circular title',
            msc_type='type-1',
            dept='dept-1',
            category='category',
            sub_category='sub-cat',
            second_sub_category='sub-cat-2',
            office_instructions='Body',
            hashtags='#tag',
            created_at=None,
            publish_status=2,
            priority='priority-1',
            created_by='EMP001',
            published_by='EMP002',
            published_on=None,
            is_superseeded=False,
            superseeded_by=None,
            is_active=True,
            is_deleted=False,
            attachment_name='circular.pdf',
            attachment_path='uploads/circular.pdf',
        )

        response = get_notification_details_by_sr_no(
            self.factory.get('/api/circular/api/submitted/KSM/Circular/Technical/2026-0001/'),
            'KSM/Circular/Technical/2026-0001',
        )

        self.assertEqual(response.status_code, 200)
        mock_lookup.assert_called_once_with('KSM/Circular/Technical/2026-0001')

    @patch('modules.circular.circular_office.views.MscNotification')
    @patch('modules.circular.circular_office.views._get_latest_notification_record_by_sr_no')
    def test_create_delivery_records_uses_latest_helper(self, mock_lookup, mock_notification_model):
        mock_lookup.return_value = SimpleNamespace(
            id='note-1',
            sr_no='KSM/Circular/Technical/2026-0001',
        )

        response = create_delivery_records(
            self.factory.post(
                '/api/circular/api/notifications/create-delivery-records/',
                {
                    'notification_sr_no': 'KSM/Circular/Technical/2026-0001',
                    'crew_ids': ['CREW001', 'CREW002'],
                },
                format='json',
            )
        )

        self.assertEqual(response.status_code, 200)
        mock_lookup.assert_called_once_with('KSM/Circular/Technical/2026-0001')
        self.assertEqual(mock_notification_model.call_count, 2)


class CircularAttachmentValidationTests(SimpleTestCase):
    def test_extract_uploaded_pdf_attachments_accepts_up_to_maximum(self):
        request_files = MultiValueDict(
            {
                'attachment': [
                    SimpleUploadedFile('one.pdf', b'%PDF-1.4', content_type='application/pdf'),
                    SimpleUploadedFile('two.pdf', b'%PDF-1.4', content_type='application/pdf'),
                    SimpleUploadedFile('three.pdf', b'%PDF-1.4', content_type='application/pdf'),
                ]
            }
        )

        extracted_files = _extract_uploaded_pdf_attachments_from_request_files(request_files)
        self.assertEqual(len(extracted_files), MAX_CIRCULAR_ATTACHMENT_FILES)

    def test_extract_uploaded_pdf_attachments_rejects_more_than_maximum(self):
        request_files = MultiValueDict(
            {
                'attachment': [
                    SimpleUploadedFile('one.pdf', b'%PDF-1.4', content_type='application/pdf'),
                    SimpleUploadedFile('two.pdf', b'%PDF-1.4', content_type='application/pdf'),
                    SimpleUploadedFile('three.pdf', b'%PDF-1.4', content_type='application/pdf'),
                    SimpleUploadedFile('four.pdf', b'%PDF-1.4', content_type='application/pdf'),
                ]
            }
        )

        with self.assertRaises(CircularAttachmentValidationError) as exc_info:
            _extract_uploaded_pdf_attachments_from_request_files(request_files)

        self.assertIn('maximum', str(exc_info.exception).lower())

    def test_extract_uploaded_pdf_attachments_rejects_non_pdf(self):
        request_files = MultiValueDict(
            {
                'attachment': [
                    SimpleUploadedFile('one.pdf', b'%PDF-1.4', content_type='application/pdf'),
                    SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain'),
                ]
            }
        )

        with self.assertRaises(CircularAttachmentValidationError) as exc_info:
            _extract_uploaded_pdf_attachments_from_request_files(request_files)

        self.assertIn('only pdf', str(exc_info.exception).lower())

    @patch(
        'modules.circular.circular_office.views.PdfReader',
        side_effect=DependencyError('PyCryptodome is required for AES algorithm'),
    )
    def test_open_uploaded_pdf_reader_surfaces_attachment_validation_error(self, mock_pdf_reader):
        with self.assertRaises(CircularAttachmentValidationError) as exc_info:
            _open_uploaded_pdf_reader(io.BytesIO(b'%PDF-1.4'))

        self.assertIn('encryption', str(exc_info.exception).lower())
        mock_pdf_reader.assert_called_once()
