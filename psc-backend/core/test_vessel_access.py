"""
Tests for core/vessel_access.py.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.accounts.models import RoleCodes
from core.vessel_access import (
    apply_office_vessel_filter,
    get_office_user_identifiers,
    get_office_user_vessel_ids,
    has_global_office_vessel_access,
)


def make_user(
    *,
    role,
    user_type,
    login_id='pic.user',
    employee_id='EMP001',
    user_id='usr-1',
    has_global_vessel_access=None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        login_id=login_id,
        employee_id=employee_id,
        username=login_id,
        has_global_vessel_access=has_global_vessel_access,
        is_authenticated=True,
    )


class TestGetOfficeUserIdentifiers(TestCase):
    def test_collects_unique_non_empty_identifiers(self):
        user = make_user(
            role=RoleCodes.OFFICE_PIC,
            user_type='OFFICE',
            login_id='pic.user',
            employee_id='EMP001',
            user_id='EMP001',  # duplicate on purpose
        )

        result = get_office_user_identifiers(user)

        self.assertEqual(result, ['pic.user', 'EMP001'])


class TestGetOfficeUserVesselIds(TestCase):
    @patch('core.vessel_access.MasterRoleByVessel.objects')
    def test_returns_assigned_vessel_ids(self, mock_objects):
        vessel_ids = [uuid.uuid4(), uuid.uuid4()]

        base_qs = MagicMock()
        filtered_qs = MagicMock()
        filtered_qs.values_list.return_value = vessel_ids

        mock_objects.filter.return_value = base_qs
        base_qs.filter.return_value = filtered_qs

        result = get_office_user_vessel_ids(['EMP001'])

        self.assertEqual(result, vessel_ids)
        mock_objects.filter.assert_called_once_with(
            IsActive=True,
            is_deleted=False,
        )
        base_qs.filter.assert_called_once()

    def test_none_identifiers_returns_none(self):
        result = get_office_user_vessel_ids(None)
        self.assertIsNone(result)

    @patch('core.vessel_access.MasterRoleByVessel.objects')
    def test_handles_exception_gracefully(self, mock_objects):
        mock_objects.filter.side_effect = Exception('DB error')

        result = get_office_user_vessel_ids(['EMP001'])

        self.assertEqual(result, [])


class TestHasGlobalOfficeVesselAccess(TestCase):
    @patch('core.vessel_access.get_office_user_identifiers')
    @patch('apps.accounts.utils.get_office_global_reviewer_role')
    def test_explicit_true_claim_short_circuits(self, mock_get_role, mock_ids):
        user = make_user(
            role=RoleCodes.OFFICE_PIC,
            user_type='OFFICE',
            has_global_vessel_access=True,
        )

        self.assertTrue(has_global_office_vessel_access(user))
        mock_ids.assert_not_called()
        mock_get_role.assert_not_called()

    @patch('core.vessel_access.get_office_user_identifiers')
    @patch('apps.accounts.utils.get_office_global_reviewer_role')
    def test_explicit_false_claim_short_circuits(self, mock_get_role, mock_ids):
        user = make_user(
            role=RoleCodes.OFFICE_PIC,
            user_type='OFFICE',
            has_global_vessel_access=False,
        )

        self.assertFalse(has_global_office_vessel_access(user))
        mock_ids.assert_not_called()
        mock_get_role.assert_not_called()

    def test_dpa_role_fallback_is_global(self):
        user = make_user(
            role=RoleCodes.DPA,
            user_type='OFFICE',
            has_global_vessel_access=None,
        )

        self.assertTrue(has_global_office_vessel_access(user))

    @patch('apps.accounts.utils.get_office_global_reviewer_role')
    def test_db_lookup_supports_old_tokens(self, mock_get_role):
        mock_get_role.return_value = RoleCodes.OFFICE_PIC
        user = make_user(
            role=RoleCodes.OFFICE_PIC,
            user_type='OFFICE',
            has_global_vessel_access=None,
        )

        self.assertTrue(has_global_office_vessel_access(user))
        mock_get_role.assert_called_once()


class TestApplyOfficeVesselFilter(TestCase):
    def _mock_queryset(self):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.none.return_value = MagicMock()
        return qs

    def test_vessel_user_passthrough(self):
        user = make_user(role=RoleCodes.VESSEL_MASTER, user_type='VESSEL')
        qs = self._mock_queryset()

        result = apply_office_vessel_filter(qs, user)

        self.assertIs(result, qs)
        qs.filter.assert_not_called()

    def test_global_office_passthrough(self):
        user = make_user(
            role=RoleCodes.OFFICE_PIC,
            user_type='OFFICE',
            has_global_vessel_access=True,
        )
        qs = self._mock_queryset()

        result = apply_office_vessel_filter(qs, user)

        self.assertIs(result, qs)
        qs.filter.assert_not_called()

    @patch('core.vessel_access.get_office_user_vessel_ids')
    def test_office_user_filtered_to_assigned_vessels(self, mock_get_ids):
        vessel_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_get_ids.return_value = vessel_ids
        user = make_user(
            role=RoleCodes.OFFICE_PIC,
            user_type='OFFICE',
            has_global_vessel_access=False,
        )
        qs = self._mock_queryset()

        result = apply_office_vessel_filter(qs, user)

        qs.filter.assert_called_once_with(vessel_id__in=vessel_ids)
        self.assertEqual(result, qs.filter.return_value)

    @patch('core.vessel_access.get_office_user_vessel_ids')
    def test_no_assignments_returns_empty_queryset(self, mock_get_ids):
        mock_get_ids.return_value = []
        user = make_user(
            role=RoleCodes.OFFICE_PIC,
            user_type='OFFICE',
            has_global_vessel_access=False,
        )
        qs = self._mock_queryset()

        result = apply_office_vessel_filter(qs, user)

        qs.none.assert_called_once()
        self.assertEqual(result, qs.none.return_value)

    @patch('core.vessel_access.get_office_user_vessel_ids')
    def test_missing_mapping_table_skips_filter(self, mock_get_ids):
        mock_get_ids.return_value = None
        user = make_user(
            role=RoleCodes.OFFICE_PIC,
            user_type='OFFICE',
            has_global_vessel_access=False,
        )
        qs = self._mock_queryset()

        result = apply_office_vessel_filter(qs, user)

        self.assertIs(result, qs)
