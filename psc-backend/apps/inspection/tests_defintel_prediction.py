"""
Phase 4 tests for DefIntel prediction endpoint.
"""

import hashlib
import uuid
from datetime import date
from types import SimpleNamespace

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import RoleCodes
from apps.inspection.deficiency_models import Deficiency
from apps.inspection.defintel_models import OpenSourceDeficiencyRecord, OpenSourceImportRun
from apps.inspection.defintel_prediction import DefIntelPredictDefCodesView
from apps.inspection.models import Inspection


def make_user(vessel_id):
    return SimpleNamespace(
        id='vm-1',
        role=RoleCodes.VESSEL_MASTER,
        user_type='VESSEL',
        vessel_id=str(vessel_id),
        display_name='Vessel Master',
        username='vessel_master',
        rank='Master',
        employee_id=None,
        is_authenticated=True,
    )


def make_office_user():
    return SimpleNamespace(
        id='office-1',
        role=RoleCodes.OFFICE_PIC,
        user_type='OFFICE',
        vessel_id=None,
        display_name='Office PIC',
        username='office_pic',
        rank=None,
        employee_id='EMP001',
        is_authenticated=True,
    )


class TestDefIntelPredictionPhase4(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = DefIntelPredictDefCodesView.as_view()
        self.vessel_id = uuid.uuid4()
        self.other_vessel_id = uuid.uuid4()
        self.user = make_user(self.vessel_id)
        self.today = date.today()

        self._create_internal_data()
        self._create_opensource_data()

    def _create_inspection(self, *, vessel_id, inspection_date, port_place, mou_id):
        return Inspection.objects.create(
            vessel_id=vessel_id,
            inspection_type='PSC',
            psc_subtype='INITIAL',
            inspection_date=inspection_date,
            port_place=port_place,
            country='Singapore',
            mou_id=mou_id,
            inspector_name='Inspector',
            created_by='seed-user',
        )

    def _create_deficiency(self, *, inspection, def_code, action_code):
        Deficiency.objects.create(
            inspection=inspection,
            def_code_id=def_code,
            def_code=def_code,
            description='Sample deficiency',
            action_code_id=action_code,
            action_code=str(action_code),
            sequence_no=1,
        )

    def _create_internal_data(self):
        singapore_recent = self._create_inspection(
            vessel_id=self.vessel_id,
            inspection_date=date(self.today.year, max(1, self.today.month - 1), 10),
            port_place='Singapore',
            mou_id='Tokyo',
        )
        self._create_deficiency(inspection=singapore_recent, def_code='01101', action_code=30)

        busan_recent = self._create_inspection(
            vessel_id=self.vessel_id,
            inspection_date=date(self.today.year, max(1, self.today.month - 1), 12),
            port_place='Busan',
            mou_id='Tokyo',
        )
        self._create_deficiency(inspection=busan_recent, def_code='01234', action_code=17)

        singapore_old = self._create_inspection(
            vessel_id=self.vessel_id,
            inspection_date=date(self.today.year - 3, 1, 10),
            port_place='Singapore',
            mou_id='Tokyo',
        )
        self._create_deficiency(inspection=singapore_old, def_code='09999', action_code=30)

        other_vessel_recent = self._create_inspection(
            vessel_id=self.other_vessel_id,
            inspection_date=date(self.today.year, max(1, self.today.month - 1), 8),
            port_place='Singapore',
            mou_id='Tokyo',
        )
        self._create_deficiency(inspection=other_vessel_recent, def_code='08888', action_code=30)

    def _create_opensource_data(self):
        import_run = OpenSourceImportRun.objects.create(
            uploaded_by='vm-1',
            filename='monthly.xlsx',
            file_hash=hashlib.sha256(b'prediction').hexdigest(),
            total_rows=3,
            valid_rows=3,
            inserted_rows=3,
            duplicate_rows=0,
            invalid_rows=0,
        )

        records = [
            (self.today.year, '01101', 30, 'SINGAPORE', 'TOKYO'),
            (self.today.year, '01234', 17, 'SINGAPORE', 'TOKYO'),
            (self.today.year - 3, '03333', 30, 'SINGAPORE', 'TOKYO'),
        ]
        for year, def_code, action_code, port, mou in records:
            dedup_source = f'{year}|{def_code}|{action_code}|{port}|{mou}'
            OpenSourceDeficiencyRecord.objects.create(
                import_run=import_run,
                year=year,
                def_code_norm=def_code,
                action_code_norm=action_code,
                port_norm=port,
                mou_norm=mou,
                country_norm='SINGAPORE',
                description_raw='OpenSource sample',
                dedup_key_hash=hashlib.sha256(dedup_source.encode('utf-8')).hexdigest(),
            )

    def _get(self, query_string):
        request = self.factory.get(f'/api/psc/reports/defintel/predict-defcodes/{query_string}')
        force_authenticate(request, user=self.user)
        return self.view(request)

    def test_default_window_last_24_months_aggregates_internal_and_opensource(self):
        response = self._get('?context=PORT&port= singapore &top_n=10')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertEqual(data['window'], 'LAST_24_MONTHS')
        self.assertEqual(data['context'], 'PORT')
        self.assertEqual(data['context_value'], 'SINGAPORE')

        rows = data['rows']
        self.assertEqual([row['def_code'] for row in rows], ['01101', '01234'])
        self.assertEqual(rows[0]['count_context'], 2)
        self.assertEqual(rows[0]['count_global'], 2)
        self.assertEqual(rows[0]['last_seen_date'], date(self.today.year, max(1, self.today.month - 1), 10).isoformat())
        self.assertAlmostEqual(rows[0]['probability'], round(52 / 103, 6), places=6)
        self.assertEqual(rows[1]['count_context'], 1)
        self.assertEqual(rows[1]['count_global'], 2)
        self.assertAlmostEqual(rows[1]['probability'], round(51 / 103, 6), places=6)
        self.assertIn('window_fallback', data)
        probabilities = [row['probability'] for row in rows]
        self.assertEqual(probabilities, sorted(probabilities, reverse=True))

    def test_all_time_window_includes_older_internal_rows(self):
        response = self._get('?context=PORT&port=Singapore&window=ALL_TIME&top_n=10')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = response.data['data']['rows']
        returned_codes = [row['def_code'] for row in rows]
        self.assertIn('09999', returned_codes)
        self.assertIn('03333', returned_codes)
        old_row = next(row for row in rows if row['def_code'] == '09999')
        self.assertEqual(old_row['count_context'], 1)
        self.assertEqual(old_row['count_global'], 1)
        self.assertEqual(old_row['last_seen_date'], date(self.today.year - 3, 1, 10).isoformat())
        opensource_only_row = next(row for row in rows if row['def_code'] == '03333')
        self.assertIsNone(opensource_only_row['last_seen_date'])

    def test_mou_context_last_24_months(self):
        response = self._get('?context=MOU&mou= tokyo &window=LAST_24_MONTHS&top_n=10')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']
        self.assertEqual(data['context'], 'MOU')
        self.assertEqual(data['context_value'], 'TOKYO')
        self.assertEqual(data['window'], 'LAST_24_MONTHS')

        rows = data['rows']
        self.assertEqual([row['def_code'] for row in rows], ['01101', '01234'])
        self.assertEqual(rows[0]['count_context'], 2)
        self.assertEqual(rows[1]['count_context'], 2)
        self.assertEqual(rows[0]['count_global'], 2)
        self.assertEqual(rows[1]['count_global'], 2)
        self.assertEqual(rows[0]['probability'], 0.5)
        self.assertEqual(rows[1]['probability'], 0.5)

    def test_mou_context_all_time_window(self):
        response = self._get('?context=MOU&mou=Tokyo&window=ALL_TIME&top_n=10')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = response.data['data']['rows']
        self.assertEqual([row['def_code'] for row in rows], ['01101', '01234', '03333', '09999'])
        opensource_only_row = next(row for row in rows if row['def_code'] == '03333')
        self.assertIsNone(opensource_only_row['last_seen_date'])
        internal_row = next(row for row in rows if row['def_code'] == '09999')
        self.assertEqual(internal_row['last_seen_date'], date(self.today.year - 3, 1, 10).isoformat())

    def test_validation_requires_port_for_port_context(self):
        response = self._get('?context=PORT')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'VALIDATION_ERROR')
        self.assertIn('port', response.data['details'])

    def test_validation_requires_mou_for_mou_context(self):
        response = self._get('?context=MOU')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'VALIDATION_ERROR')
        self.assertIn('mou', response.data['details'])

    def test_validation_requires_context(self):
        response = self._get('?port=Singapore')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'VALIDATION_ERROR')
        self.assertIn('context', response.data['details'])

    def test_validation_rejects_top_n_over_max(self):
        response = self._get('?context=PORT&port=Singapore&top_n=101')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'VALIDATION_ERROR')
        self.assertIn('top_n', response.data['details'])

    def test_office_user_can_access_prediction(self):
        self.user = make_office_user()
        response = self._get('?context=PORT&port=Singapore&top_n=10')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rows', response.data['data'])
