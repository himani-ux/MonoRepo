"""
Tests for DEF vessel-side workflow (workflow.py + deficiency views).

PRD Reference: PRD.md FEAT-DEF-001 through FEAT-DEF-005
Validation Reference: BACKEND_STRUCTURE.md Section 10.4

Tests the state machine, rank classification, UUID helpers,
and the three untested views: DeficiencyWorkflowTransitionView,
BulkDeficiencySubmitView, DeficiencyListFilteredView.
"""

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import RoleCodes
from apps.car.models import ActivityHistory
from apps.inspection.deficiency_models import CAR, CARStatus, Deficiency, DefStatus
from apps.inspection.models import Inspection, InspectionStatus
from apps.inspection.deficiency_views import (
    DeficiencyWorkflowTransitionView,
    BulkDeficiencySubmitView,
    DeficiencyListFilteredView,
)
from apps.inspection.workflow import (
    classify_rank,
    validate_transition,
    _normalize_uuid,
    _uuid_match,
    RANK_MASTER,
    RANK_CE,
    RANK_CO,
    RANK_2E,
    RANK_OTHER,
)


# ============================================================================
# Helpers
# ============================================================================

def make_user(
    *,
    role: str,
    user_type: str,
    vessel_id: str | None = None,
    user_id: str = "test-user",
    display_name: str = "Test User",
    rank: str | None = None,
    crew_id: str | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        vessel_id=vessel_id,
        display_name=display_name,
        username=display_name.lower().replace(" ", "_"),
        is_authenticated=True,
        rank=rank,
        crew_id=crew_id or user_id,
        employee_id=user_id,
    )


# ============================================================================
# TestClassifyRank — pure function tests
# ============================================================================

class TestClassifyRank(TestCase):
    """Tests for classify_rank() in workflow.py."""

    def test_master_keyword(self):
        self.assertEqual(classify_rank('Master'), RANK_MASTER)

    def test_captain_keyword(self):
        self.assertEqual(classify_rank('Captain'), RANK_MASTER)

    def test_master_case_insensitive(self):
        self.assertEqual(classify_rank('MASTER'), RANK_MASTER)

    def test_master_mixed_case(self):
        self.assertEqual(classify_rank('Ship Master'), RANK_MASTER)

    def test_chief_engineer(self):
        self.assertEqual(classify_rank('Chief Engineer'), RANK_CE)

    def test_ce_abbreviation(self):
        self.assertEqual(classify_rank('C/E'), RANK_CE)

    def test_chief_officer(self):
        self.assertEqual(classify_rank('Chief Officer'), RANK_CO)

    def test_chief_mate(self):
        self.assertEqual(classify_rank('Chief Mate'), RANK_CO)

    def test_co_abbreviation(self):
        self.assertEqual(classify_rank('C/O'), RANK_CO)

    def test_second_engineer(self):
        self.assertEqual(classify_rank('Second Engineer'), RANK_2E)

    def test_2nd_engineer(self):
        self.assertEqual(classify_rank('2nd Engineer'), RANK_2E)

    def test_2e_abbreviation(self):
        self.assertEqual(classify_rank('2/E'), RANK_2E)

    def test_bosun_returns_other(self):
        self.assertEqual(classify_rank('Bosun'), RANK_OTHER)

    def test_none_returns_other(self):
        self.assertEqual(classify_rank(None), RANK_OTHER)

    def test_empty_returns_other(self):
        self.assertEqual(classify_rank(''), RANK_OTHER)

    def test_whitespace_returns_other(self):
        self.assertEqual(classify_rank('   '), RANK_OTHER)


# ============================================================================
# TestNormalizeUuid — pure function tests
# ============================================================================

class TestNormalizeUuid(TestCase):
    """Tests for _normalize_uuid() and _uuid_match()."""

    def test_hyphenated_preserved(self):
        uid = '12345678-1234-1234-1234-123456789012'
        self.assertEqual(_normalize_uuid(uid), uid)

    def test_char32_converted(self):
        char32 = '12345678123412341234123456789012'
        self.assertEqual(
            _normalize_uuid(char32),
            '12345678-1234-1234-1234-123456789012',
        )

    def test_none_returns_empty(self):
        self.assertEqual(_normalize_uuid(None), '')

    def test_uuid_match_across_formats(self):
        hyphenated = '12345678-1234-1234-1234-123456789012'
        char32 = '12345678123412341234123456789012'
        self.assertTrue(_uuid_match(hyphenated, char32))

    def test_uuid_match_none_returns_false(self):
        self.assertFalse(_uuid_match(None, '12345678-1234-1234-1234-123456789012'))
        self.assertFalse(_uuid_match('12345678-1234-1234-1234-123456789012', None))


# ============================================================================
# TestValidateTransition — state machine tests
# ============================================================================

class TestValidateTransition(TestCase):
    """Tests for validate_transition() in workflow.py."""

    def setUp(self):
        self.vessel_id = uuid.uuid4()
        self.owner_id = str(uuid.uuid4())
        self.reviewer_id = str(uuid.uuid4())
        self.master_id = str(uuid.uuid4())

        # Mock deficiency object
        self.deficiency = SimpleNamespace(
            assigned_crew_id=self.owner_id,
            reviewer_crew_id=self.reviewer_id,
        )

    def _make_user(self, *, rank=None, crew_id=None):
        return SimpleNamespace(
            id=crew_id or str(uuid.uuid4()),
            crew_id=crew_id or str(uuid.uuid4()),
            rank=rank,
        )

    # --- Valid transitions ---

    def test_allocated_to_in_progress_by_owner(self):
        user = self._make_user(crew_id=self.owner_id)
        valid, err = validate_transition(
            DefStatus.ALLOCATED, DefStatus.IN_PROGRESS, user, self.deficiency,
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_in_progress_to_completed_by_owner(self):
        user = self._make_user(crew_id=self.owner_id)
        valid, err = validate_transition(
            DefStatus.IN_PROGRESS, DefStatus.COMPLETED, user, self.deficiency,
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_completed_to_under_review_by_reviewer(self):
        user = self._make_user(crew_id=self.reviewer_id)
        valid, err = validate_transition(
            DefStatus.COMPLETED, DefStatus.UNDER_REVIEW, user, self.deficiency,
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_under_review_to_approved_by_reviewer(self):
        user = self._make_user(crew_id=self.reviewer_id)
        valid, err = validate_transition(
            DefStatus.UNDER_REVIEW, DefStatus.APPROVED, user, self.deficiency,
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_approved_to_submitted_by_master(self):
        user = self._make_user(rank='Master')
        valid, err = validate_transition(
            DefStatus.APPROVED, DefStatus.SUBMITTED, user, self.deficiency,
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_under_review_to_in_progress_rework(self):
        """Rework path: reviewer sends back to IN_PROGRESS."""
        user = self._make_user(crew_id=self.reviewer_id)
        valid, err = validate_transition(
            DefStatus.UNDER_REVIEW, DefStatus.IN_PROGRESS, user, self.deficiency,
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    # --- Master override ---

    def test_master_can_act_as_owner(self):
        user = self._make_user(rank='Master')
        valid, err = validate_transition(
            DefStatus.ALLOCATED, DefStatus.IN_PROGRESS, user, self.deficiency,
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_master_can_act_as_reviewer(self):
        user = self._make_user(rank='Captain')
        valid, err = validate_transition(
            DefStatus.COMPLETED, DefStatus.UNDER_REVIEW, user, self.deficiency,
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    # --- Invalid transitions ---

    def test_backwards_transition_rejected(self):
        user = self._make_user(crew_id=self.owner_id)
        valid, err = validate_transition(
            DefStatus.COMPLETED, DefStatus.ALLOCATED, user, self.deficiency,
        )
        self.assertFalse(valid)
        self.assertIn('not allowed', err)

    def test_skip_transition_rejected(self):
        user = self._make_user(crew_id=self.owner_id, rank='Master')
        valid, err = validate_transition(
            DefStatus.ALLOCATED, DefStatus.COMPLETED, user, self.deficiency,
        )
        self.assertFalse(valid)
        self.assertIn('not allowed', err)

    def test_submitted_is_terminal(self):
        user = self._make_user(rank='Master')
        valid, err = validate_transition(
            DefStatus.SUBMITTED, DefStatus.APPROVED, user, self.deficiency,
        )
        self.assertFalse(valid)

    # --- Actor enforcement ---

    def test_wrong_crew_cannot_act_as_owner(self):
        user = self._make_user(crew_id=str(uuid.uuid4()))
        valid, err = validate_transition(
            DefStatus.ALLOCATED, DefStatus.IN_PROGRESS, user, self.deficiency,
        )
        self.assertFalse(valid)
        self.assertIn('assigned crew', err)

    def test_wrong_crew_cannot_act_as_reviewer(self):
        user = self._make_user(crew_id=str(uuid.uuid4()))
        valid, err = validate_transition(
            DefStatus.COMPLETED, DefStatus.UNDER_REVIEW, user, self.deficiency,
        )
        self.assertFalse(valid)
        self.assertIn('reviewer', err.lower())

    def test_non_master_cannot_submit(self):
        user = self._make_user(rank='2nd Engineer')
        valid, err = validate_transition(
            DefStatus.APPROVED, DefStatus.SUBMITTED, user, self.deficiency,
        )
        self.assertFalse(valid)
        self.assertIn('Master', err)


# ============================================================================
# TestDeficiencyWorkflowTransitionView — integration tests
# ============================================================================

class BaseDefWorkflowTestCase(TestCase):
    """Shared setUp for workflow view tests.

    Patches unmanaged-table lookups used by DeficiencyDetailSerializer
    and DeficiencyListSerializer (PSCDefCode, PSCActionCode, HRM501).
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.vessel_id = uuid.uuid4()
        self.owner_id = uuid.uuid4()
        self.reviewer_id = uuid.uuid4()
        self.master_id = uuid.uuid4()

        # Patch unmanaged table lookups used by serializers
        p1 = patch(
            'apps.inspection.deficiency_serializers.PSCDefCode.objects.get',
            return_value=SimpleNamespace(def_code='10101', def_name='Certificate issue'),
        )
        p2 = patch(
            'apps.inspection.deficiency_serializers.PSCActionCode.objects.get',
            return_value=SimpleNamespace(action_code=30, definition='Rectify'),
        )
        p3 = patch('apps.accounts.models.HRM501.objects')
        self.mock_def_code = p1.start()
        self.mock_action_code = p2.start()
        self.mock_hrm501 = p3.start()
        self.mock_hrm501.extra.return_value.first.return_value = None
        self.addCleanup(p1.stop)
        self.addCleanup(p2.stop)
        self.addCleanup(p3.stop)

        self.vessel_master = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type='VESSEL',
            vessel_id=str(self.vessel_id),
            user_id=str(self.master_id),
            display_name='Vessel Master',
            rank='Master',
            crew_id=str(self.master_id),
        )
        self.vessel_crew_owner = make_user(
            role=RoleCodes.VESSEL_CREW,
            user_type='VESSEL',
            vessel_id=str(self.vessel_id),
            user_id=str(self.owner_id),
            display_name='Crew Owner',
            rank='2nd Engineer',
            crew_id=str(self.owner_id),
        )
        self.vessel_crew_reviewer = make_user(
            role=RoleCodes.VESSEL_CREW,
            user_type='VESSEL',
            vessel_id=str(self.vessel_id),
            user_id=str(self.reviewer_id),
            display_name='Crew Reviewer',
            rank='Chief Engineer',
            crew_id=str(self.reviewer_id),
        )
        self.wrong_vessel_user = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type='VESSEL',
            vessel_id=str(uuid.uuid4()),
            user_id='wrong-vessel',
            display_name='Wrong Vessel',
            rank='Master',
        )

    def create_inspection(self, **overrides):
        defaults = {
            'vessel_id': self.vessel_id,
            'inspection_type': 'PSC',
            'psc_subtype': 'INITIAL',
            'inspection_date': date.today(),
            'port_place': 'Singapore',
            'country': 'Singapore',
            'mou_id': 'TOKYO',
            'authority': 'PSC Authority',
            'inspector_name': 'Inspector',
            'report_reference': 'REF-001',
            'is_detention': False,
        }
        defaults.update(overrides)
        return Inspection.objects.create(**defaults)

    def create_deficiency(self, inspection, **overrides):
        car = CAR.objects.create(
            car_number=f"PSC-{date.today().year}-{uuid.uuid4().hex[:6].upper()}",
            status='DRAFT',
        )
        defaults = {
            'inspection': inspection,
            'def_code_id': '10101',
            'def_code': '10101',
            'description': 'Test deficiency',
            'def_status': DefStatus.ALLOCATED,
            'assigned_crew_id': self.owner_id,
            'reviewer_crew_id': self.reviewer_id,
            'owner_rank': '2nd Engineer',
            'owner_name': 'Crew Owner',
            'reviewer_rank': 'Chief Engineer',
            'reviewer_name': 'Crew Reviewer',
            'car': car,
        }
        defaults.update(overrides)
        return Deficiency.objects.create(**defaults)


class TestDeficiencyWorkflowTransitionView(BaseDefWorkflowTestCase):
    """POST /api/psc/deficiencies/{id}/workflow/ tests."""

    def test_happy_path_owner_starts_work(self):
        inspection = self.create_inspection()
        deficiency = self.create_deficiency(inspection, def_status=DefStatus.ALLOCATED)

        view = DeficiencyWorkflowTransitionView.as_view()
        request = self.factory.post(
            f'/api/psc/deficiencies/{deficiency.id}/workflow/',
            {'target_status': DefStatus.IN_PROGRESS},
            format='json',
        )
        force_authenticate(request, user=self.vessel_crew_owner)
        response = view(request, id=deficiency.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        deficiency.refresh_from_db()
        self.assertEqual(deficiency.def_status, DefStatus.IN_PROGRESS)

    def test_activity_history_created(self):
        inspection = self.create_inspection()
        deficiency = self.create_deficiency(inspection, def_status=DefStatus.ALLOCATED)

        view = DeficiencyWorkflowTransitionView.as_view()
        request = self.factory.post(
            f'/api/psc/deficiencies/{deficiency.id}/workflow/',
            {'target_status': DefStatus.IN_PROGRESS},
            format='json',
        )
        force_authenticate(request, user=self.vessel_crew_owner)
        view(request, id=deficiency.id)

        activity = ActivityHistory.objects.filter(
            entity_id=deficiency.id,
            event_type='DEF_IN_PROGRESS',
        ).first()
        self.assertIsNotNone(activity)
        self.assertIn('ALLOCATED', activity.event_description)
        self.assertIn('IN_PROGRESS', activity.event_description)

    def test_comment_included_in_activity(self):
        inspection = self.create_inspection()
        deficiency = self.create_deficiency(inspection, def_status=DefStatus.ALLOCATED)

        view = DeficiencyWorkflowTransitionView.as_view()
        request = self.factory.post(
            f'/api/psc/deficiencies/{deficiency.id}/workflow/',
            {'target_status': DefStatus.IN_PROGRESS, 'comment': 'Starting work now'},
            format='json',
        )
        force_authenticate(request, user=self.vessel_crew_owner)
        view(request, id=deficiency.id)

        activity = ActivityHistory.objects.filter(
            entity_id=deficiency.id,
            event_type='DEF_IN_PROGRESS',
        ).first()
        self.assertIn('Starting work now', activity.event_description)

    def test_submitted_updates_car_status(self):
        inspection = self.create_inspection()
        deficiency = self.create_deficiency(inspection, def_status=DefStatus.APPROVED)

        view = DeficiencyWorkflowTransitionView.as_view()
        request = self.factory.post(
            f'/api/psc/deficiencies/{deficiency.id}/workflow/',
            {'target_status': DefStatus.SUBMITTED},
            format='json',
        )
        force_authenticate(request, user=self.vessel_master)
        response = view(request, id=deficiency.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        deficiency.car.refresh_from_db()
        self.assertEqual(deficiency.car.status, 'SUBMITTED')

    def test_master_can_transition_on_behalf_of_owner(self):
        inspection = self.create_inspection()
        deficiency = self.create_deficiency(inspection, def_status=DefStatus.ALLOCATED)

        view = DeficiencyWorkflowTransitionView.as_view()
        request = self.factory.post(
            f'/api/psc/deficiencies/{deficiency.id}/workflow/',
            {'target_status': DefStatus.IN_PROGRESS},
            format='json',
        )
        force_authenticate(request, user=self.vessel_master)
        response = view(request, id=deficiency.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_wrong_vessel_rejected(self):
        inspection = self.create_inspection()
        deficiency = self.create_deficiency(inspection, def_status=DefStatus.ALLOCATED)

        view = DeficiencyWorkflowTransitionView.as_view()
        request = self.factory.post(
            f'/api/psc/deficiencies/{deficiency.id}/workflow/',
            {'target_status': DefStatus.IN_PROGRESS},
            format='json',
        )
        force_authenticate(request, user=self.wrong_vessel_user)
        response = view(request, id=deficiency.id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_target_status_rejected(self):
        inspection = self.create_inspection()
        deficiency = self.create_deficiency(inspection, def_status=DefStatus.ALLOCATED)

        view = DeficiencyWorkflowTransitionView.as_view()
        request = self.factory.post(
            f'/api/psc/deficiencies/{deficiency.id}/workflow/',
            {'target_status': DefStatus.APPROVED},
            format='json',
        )
        force_authenticate(request, user=self.vessel_crew_owner)
        response = view(request, id=deficiency.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_rejected(self):
        inspection = self.create_inspection()
        deficiency = self.create_deficiency(inspection, def_status=DefStatus.ALLOCATED)

        view = DeficiencyWorkflowTransitionView.as_view()
        request = self.factory.post(
            f'/api/psc/deficiencies/{deficiency.id}/workflow/',
            {'target_status': DefStatus.IN_PROGRESS},
            format='json',
        )
        # No authentication
        response = view(request, id=deficiency.id)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_nonexistent_deficiency_returns_404(self):
        view = DeficiencyWorkflowTransitionView.as_view()
        fake_id = uuid.uuid4()
        request = self.factory.post(
            f'/api/psc/deficiencies/{fake_id}/workflow/',
            {'target_status': DefStatus.IN_PROGRESS},
            format='json',
        )
        force_authenticate(request, user=self.vessel_master)
        response = view(request, id=fake_id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================================
# TestBulkDeficiencySubmitView
# ============================================================================

class TestBulkDeficiencySubmitView(BaseDefWorkflowTestCase):
    """POST /api/psc/inspections/{id}/deficiencies/bulk-submit/ tests."""

    @staticmethod
    def _set_car_pending_master_review(*deficiencies):
        """Align test fixtures with current bulk-submit precondition."""
        for deficiency in deficiencies:
            deficiency.car.status = CARStatus.PENDING_MASTER_REVIEW
            deficiency.car.save(update_fields=['status'])

    def test_happy_path_bulk_submit(self):
        inspection = self.create_inspection()
        d1 = self.create_deficiency(inspection, def_status=DefStatus.APPROVED)
        d2 = self.create_deficiency(inspection, def_status=DefStatus.APPROVED)
        self._set_car_pending_master_review(d1, d2)

        view = BulkDeficiencySubmitView.as_view()
        request = self.factory.post(
            f'/api/psc/inspections/{inspection.id}/deficiencies/bulk-submit/',
            {'deficiency_ids': [str(d1.id), str(d2.id)]},
            format='json',
        )
        force_authenticate(request, user=self.vessel_master)
        response = view(request, inspection_id=inspection.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        d1.refresh_from_db()
        d2.refresh_from_db()
        self.assertEqual(d1.def_status, DefStatus.SUBMITTED)
        self.assertEqual(d2.def_status, DefStatus.SUBMITTED)

    def test_bulk_submit_updates_car_status(self):
        inspection = self.create_inspection()
        d = self.create_deficiency(inspection, def_status=DefStatus.APPROVED)
        self._set_car_pending_master_review(d)

        view = BulkDeficiencySubmitView.as_view()
        request = self.factory.post(
            f'/api/psc/inspections/{inspection.id}/deficiencies/bulk-submit/',
            {'deficiency_ids': [str(d.id)]},
            format='json',
        )
        force_authenticate(request, user=self.vessel_master)
        view(request, inspection_id=inspection.id)

        d.car.refresh_from_db()
        self.assertEqual(d.car.status, CARStatus.SUBMITTED_TO_PIC)

    def test_activity_history_created_per_deficiency(self):
        inspection = self.create_inspection()
        d1 = self.create_deficiency(inspection, def_status=DefStatus.APPROVED)
        d2 = self.create_deficiency(inspection, def_status=DefStatus.APPROVED)
        self._set_car_pending_master_review(d1, d2)

        view = BulkDeficiencySubmitView.as_view()
        request = self.factory.post(
            f'/api/psc/inspections/{inspection.id}/deficiencies/bulk-submit/',
            {'deficiency_ids': [str(d1.id), str(d2.id)]},
            format='json',
        )
        force_authenticate(request, user=self.vessel_master)
        view(request, inspection_id=inspection.id)

        activities = ActivityHistory.objects.filter(
            event_type='DEF_SUBMITTED',
            entity_id__in=[d1.id, d2.id],
        )
        self.assertEqual(activities.count(), 2)

    def test_non_approved_rejected(self):
        inspection = self.create_inspection()
        d = self.create_deficiency(inspection, def_status=DefStatus.IN_PROGRESS)

        view = BulkDeficiencySubmitView.as_view()
        request = self.factory.post(
            f'/api/psc/inspections/{inspection.id}/deficiencies/bulk-submit/',
            {'deficiency_ids': [str(d.id)]},
            format='json',
        )
        force_authenticate(request, user=self.vessel_master)
        response = view(request, inspection_id=inspection.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Pending Master Review', response.data['error'])

    def test_empty_ids_rejected(self):
        inspection = self.create_inspection()

        view = BulkDeficiencySubmitView.as_view()
        request = self.factory.post(
            f'/api/psc/inspections/{inspection.id}/deficiencies/bulk-submit/',
            {'deficiency_ids': []},
            format='json',
        )
        force_authenticate(request, user=self.vessel_master)
        response = view(request, inspection_id=inspection.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_master_can_bulk_submit(self):
        inspection = self.create_inspection()
        d = self.create_deficiency(inspection, def_status=DefStatus.APPROVED)

        view = BulkDeficiencySubmitView.as_view()
        request = self.factory.post(
            f'/api/psc/inspections/{inspection.id}/deficiencies/bulk-submit/',
            {'deficiency_ids': [str(d.id)]},
            format='json',
        )
        force_authenticate(request, user=self.vessel_crew_owner)
        response = view(request, inspection_id=inspection.id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_vessel_rejected(self):
        inspection = self.create_inspection()
        d = self.create_deficiency(inspection, def_status=DefStatus.APPROVED)

        view = BulkDeficiencySubmitView.as_view()
        request = self.factory.post(
            f'/api/psc/inspections/{inspection.id}/deficiencies/bulk-submit/',
            {'deficiency_ids': [str(d.id)]},
            format='json',
        )
        force_authenticate(request, user=self.wrong_vessel_user)
        response = view(request, inspection_id=inspection.id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_in_bulk_submit(self):
        inspection = self.create_inspection()
        d = self.create_deficiency(inspection, def_status=DefStatus.APPROVED)
        self._set_car_pending_master_review(d)

        view = BulkDeficiencySubmitView.as_view()
        request = self.factory.post(
            f'/api/psc/inspections/{inspection.id}/deficiencies/bulk-submit/',
            {'deficiency_ids': [str(d.id)], 'comment': 'All approved by Master'},
            format='json',
        )
        force_authenticate(request, user=self.vessel_master)
        view(request, inspection_id=inspection.id)

        activity = ActivityHistory.objects.filter(
            entity_id=d.id, event_type='DEF_SUBMITTED',
        ).first()
        self.assertIn('All approved by Master', activity.event_description)


# ============================================================================
# TestDeficiencyListFilteredView
# ============================================================================

class TestDeficiencyListFilteredView(BaseDefWorkflowTestCase):
    """GET /api/psc/deficiencies/ tests."""

    def test_vessel_master_sees_own_vessel(self):
        inspection = self.create_inspection()
        self.create_deficiency(inspection)

        # Create deficiency on another vessel
        other_vessel_id = uuid.uuid4()
        other_insp = self.create_inspection(vessel_id=other_vessel_id)
        Deficiency.objects.create(
            inspection=other_insp,
            def_code_id='10102',
            def_code='10102',
            description='Other vessel def',
        )

        view = DeficiencyListFilteredView.as_view()
        request = self.factory.get('/api/psc/deficiencies/')
        force_authenticate(request, user=self.vessel_master)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_crew_sees_only_assigned(self):
        inspection = self.create_inspection()
        # Assigned to crew_owner
        self.create_deficiency(inspection, assigned_crew_id=self.owner_id)
        # Assigned to someone else
        self.create_deficiency(inspection, assigned_crew_id=uuid.uuid4())

        view = DeficiencyListFilteredView.as_view()
        request = self.factory.get('/api/psc/deficiencies/')
        force_authenticate(request, user=self.vessel_crew_owner)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_status(self):
        inspection = self.create_inspection()
        self.create_deficiency(inspection, def_status=DefStatus.ALLOCATED)
        self.create_deficiency(inspection, def_status=DefStatus.IN_PROGRESS)

        view = DeficiencyListFilteredView.as_view()
        request = self.factory.get('/api/psc/deficiencies/', {'status': DefStatus.ALLOCATED})
        force_authenticate(request, user=self.vessel_master)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_awaiting_review_filter(self):
        inspection = self.create_inspection()
        self.create_deficiency(inspection, def_status=DefStatus.COMPLETED)
        self.create_deficiency(inspection, def_status=DefStatus.UNDER_REVIEW)
        self.create_deficiency(inspection, def_status=DefStatus.APPROVED)

        view = DeficiencyListFilteredView.as_view()
        request = self.factory.get('/api/psc/deficiencies/', {'awaiting_review': 'true'})
        force_authenticate(request, user=self.vessel_master)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

    def test_pagination_returns_metadata(self):
        inspection = self.create_inspection()
        self.create_deficiency(inspection)

        view = DeficiencyListFilteredView.as_view()
        request = self.factory.get('/api/psc/deficiencies/')
        force_authenticate(request, user=self.vessel_master)
        response = view(request)

        self.assertIn('pagination', response.data)
        self.assertIn('total_count', response.data['pagination'])
        self.assertIn('total_pages', response.data['pagination'])

    def test_unauthenticated_rejected(self):
        view = DeficiencyListFilteredView.as_view()
        request = self.factory.get('/api/psc/deficiencies/')
        response = view(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
