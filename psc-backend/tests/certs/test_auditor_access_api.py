from __future__ import annotations

from datetime import timedelta
import os
from unittest.mock import MagicMock, patch
import unittest
import uuid

import django
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.backends import AuthenticatedUser
from apps.certs.services.auditor_token import hash_token
from apps.certs.views.auditor_views import (
    AuditorAccessDetailView,
    AuditorAccessListCreateView,
    AuditorCertDetailView,
    AuditorPrintView,
    AuditorSignupView,
    AuditorVesselListView,
)


def make_user(
    *,
    role: str,
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    user_type: str = "OFFICE",
) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=f"{role.lower().replace(' ', '-')}-1",
        user_type=user_type,
        full_name=f"{role} User",
        role=role,
        employee_id=f"{role[:3].upper()}001",
        form_ids=form_ids or [],
        process_ids=process_ids or [],
        vessel_ids=[],
    )


def grant_row(**overrides):
    now = timezone.now()
    row = {
        "grant_id": uuid.uuid4(),
        "auditor_name": "ABS Auditor",
        "auditor_email": "auditor@example.com",
        "scope_json": '{"vesselIds": ["vessel-a"], "sections": ["SAFETY"], "certIds": []}',
        "expiry_at": now + timedelta(days=7),
        "granted_by": "marine-1",
        "granted_at": now,
        "signup_token_hash": hash_token("signup-token"),
        "signup_token_used_at": None,
        "token_secret_hash": None,
        "last_accessed_at": None,
        "revoked_via_expiry_edit": False,
    }
    row.update(overrides)
    return row


def tracked_item_row(**overrides):
    row = {
        "tracked_item_id": uuid.uuid4(),
        "vessel_id": "vessel-a",
        "catalog_id": uuid.uuid4(),
        "catalog_code": "CERT-SAFETY-001",
        "catalog_display_name": "Cargo Ship Safety Equipment Certificate",
        "catalog_short_name": "Safety Equipment",
        "catalog_submission_scope": "office_only",
        "type": "certificate",
        "validity_type": "full",
        "form_variant": "n/a",
        "cadence_months": 60,
        "cadence_custom_days": None,
        "parent_id": None,
        "relationship_type": None,
        "supersedes_id": None,
        "issue_date": "2026-01-01",
        "expiry_date": "2031-01-01",
        "anniversary_date": "2026-01-01",
        "window_open": None,
        "window_close": None,
        "last_done_date": None,
        "next_due_date": None,
        "postponed_until": None,
        "status": "ok",
        "certificate_number": "SE-001",
        "issuing_authority": "Class",
        "place_of_issue": "Singapore",
        "extension_authority": None,
        "extension_letter_pdf_id": None,
        "extension_reason": "Internal extension reason",
        "pdf_attachment_id": uuid.uuid4(),
        "pdf_missing": False,
        "source": "manual",
        "last_class_sync_id": None,
        "approval_state": "approved",
        "submitted_by": "master-1",
        "submitted_at": None,
        "approved_by": "marine-1",
        "approved_at": None,
        "rejection_reason": "Internal rejection note",
        "rejection_count": 1,
        "draft_expires_at": None,
        "lifecycle_status": "active",
        "row_version": b"\x00\x00\x00\x00\x00\x00\x00\x01",
        "version": 3,
        "created_at": None,
        "created_by": "marine-1",
        "updated_at": None,
        "updated_by": "marine-1",
    }
    row.update(overrides)
    return row


class AuditorAccessApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.dpa = make_user(role="DPA", form_ids=["CERT_F_007"], process_ids=["CERT_P_007"])
        self.marine = make_user(role="Marine Sup'tt", form_ids=["CERT_F_007"], process_ids=["CERT_P_007"])
        self.fm = make_user(role="Fleet Manager", form_ids=["CERT_F_007"], process_ids=[])
        self.tech = make_user(role="Tech Sup'tt", form_ids=["CERT_F_007"], process_ids=["CERT_P_007"])
        self.external_auditor = make_user(
            role="External Auditor",
            form_ids=["CERT_F_007"],
            process_ids=["CERT_P_007"],
            user_type="EXTERNAL_AUDITOR",
        )

    @patch("apps.certs.views.auditor_views.repository")
    def test_fm_can_list_grants_read_only_after_b_ext_01(self, repository) -> None:
        repository.list_grants.return_value = [grant_row()]
        request = self.factory.get("/api/certs/auditor-access/")
        force_authenticate(request, user=self.fm)

        response = AuditorAccessListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["auditorName"], "ABS Auditor")
        repository.list_grants.assert_called_once()

    @patch("apps.certs.views.auditor_views.repository")
    def test_fm_cannot_create_or_edit_auditor_grants(self, repository) -> None:
        create_request = self.factory.post("/api/certs/auditor-access/", {}, format="json")
        force_authenticate(create_request, user=self.fm)
        create_response = AuditorAccessListCreateView.as_view()(create_request)
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

        patch_request = self.factory.patch("/api/certs/auditor-access/grant-1/", {"expiryAt": timezone.now()}, format="json")
        force_authenticate(patch_request, user=self.fm)
        patch_response = AuditorAccessDetailView.as_view()(patch_request, grant_id=uuid.uuid4())
        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
        repository.create_grant.assert_not_called()
        repository.update_expiry.assert_not_called()

    @patch("apps.certs.views.auditor_views.repository")
    def test_external_auditor_cannot_bypass_into_internal_grant_admin(self, repository) -> None:
        list_request = self.factory.get("/api/certs/auditor-access/")
        force_authenticate(list_request, user=self.external_auditor)
        list_response = AuditorAccessListCreateView.as_view()(list_request)
        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)

        create_request = self.factory.post("/api/certs/auditor-access/", {}, format="json")
        force_authenticate(create_request, user=self.external_auditor)
        create_response = AuditorAccessListCreateView.as_view()(create_request)
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

        repository.list_grants.assert_not_called()
        repository.create_grant.assert_not_called()

    @patch("apps.certs.views.auditor_views.record_audit_event")
    @patch("apps.certs.views.auditor_views.repository")
    def test_marine_can_create_grant_with_hashed_signup_token_and_audit(self, repository, record_audit_event) -> None:
        created = grant_row()
        repository.create_grant.return_value = created
        expiry = (timezone.now() + timedelta(days=10)).isoformat()
        request = self.factory.post(
            "/api/certs/auditor-access/",
            {
                "auditorName": "ABS Auditor",
                "auditorEmail": "auditor@example.com",
                "scope": {"vesselIds": ["vessel-a"], "sections": ["SAFETY"], "certIds": []},
                "expiryAt": expiry,
            },
            format="json",
        )
        force_authenticate(request, user=self.marine)

        response = AuditorAccessListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("/api/auditor/signup/", response.data["signupUrl"])
        self.assertNotIn("signup-token", response.data["signupUrl"])
        repository.create_grant.assert_called_once()
        self.assertEqual(len(repository.create_grant.call_args.kwargs["signup_token_hash"]), 64)
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "grant_auditor_access")

    @patch("apps.certs.views.auditor_views.record_audit_event")
    @patch("apps.certs.views.auditor_views.repository")
    def test_patch_expiry_only_sets_effective_revoke_flag(self, repository, record_audit_event) -> None:
        existing = grant_row()
        updated = grant_row(expiry_at=timezone.now() - timedelta(minutes=1), revoked_via_expiry_edit=True)
        repository.get_grant.return_value = existing
        repository.update_expiry.return_value = updated
        request = self.factory.patch(
            f"/api/certs/auditor-access/{existing['grant_id']}/",
            {"expiryAt": (timezone.now() - timedelta(minutes=1)).isoformat()},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = AuditorAccessDetailView.as_view()(request, grant_id=existing["grant_id"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["revokedViaExpiryEdit"])
        repository.update_expiry.assert_called_once()
        self.assertTrue(repository.update_expiry.call_args.kwargs["revoked_via_expiry_edit"])
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "edit_auditor_access")

    @patch("apps.certs.views.auditor_views.record_audit_event")
    @patch("apps.certs.views.auditor_views.repository")
    def test_signup_token_is_one_time_and_session_secret_is_hashed(self, repository, record_audit_event) -> None:
        row = grant_row()
        repository.get_grant_by_signup_token_hash.return_value = row
        repository.mark_signup_used.return_value = grant_row(
            grant_id=row["grant_id"],
            token_secret_hash=hash_token("secret"),
            signup_token_used_at=timezone.now(),
        )
        request = self.factory.post("/api/auditor/signup/signup-token/")

        response = AuditorSignupView.as_view()(request, token="signup-token")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("sessionToken", response.data)
        self.assertNotIn("secret", response.data["sessionToken"])
        repository.mark_signup_used.assert_called_once()
        self.assertEqual(len(repository.mark_signup_used.call_args.kwargs["token_secret_hash"]), 64)
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "signup_token_used")

    @patch("apps.certs.views.auditor_views.record_audit_event")
    @patch("apps.certs.views.auditor_views.repository")
    def test_auditor_scoped_cert_detail_redacts_internal_notes_and_does_not_audit_read(self, repository, record_audit_event) -> None:
        row = grant_row(token_secret_hash=hash_token("session-secret"))
        repository.get_grant.return_value = row
        repository.get_scoped_cert.return_value = tracked_item_row()
        with patch("apps.certs.views.auditor_views.verify_session_token") as verify_session_token:
            verify_session_token.return_value = (str(row["grant_id"]), hash_token("session-secret"))
            request = self.factory.get("/api/auditor/session-token/cert/cert-1/")

            response = AuditorCertDetailView.as_view()(request, grant_token="session-token", cert_id=uuid.uuid4())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["extensionReason"], "[REDACTED - internal note]")
        self.assertEqual(response.data["rejectionReason"], "[REDACTED - internal note]")
        self.assertNotIn("auditEvents", response.data)
        record_audit_event.assert_not_called()

    @patch("apps.certs.views.auditor_views.record_audit_event")
    @patch("apps.certs.views.auditor_views.repository")
    def test_auditor_token_tamper_or_secret_mismatch_returns_terminal_expired(self, repository, record_audit_event) -> None:
        row = grant_row(token_secret_hash=hash_token("expected-secret"))
        repository.get_grant.return_value = row

        bad_signature_request = self.factory.get("/api/auditor/not-a-valid-token/vessels/")
        bad_signature_response = AuditorVesselListView.as_view()(bad_signature_request, grant_token="not-a-valid-token")
        self.assertEqual(bad_signature_response.status_code, status.HTTP_410_GONE)
        self.assertIn("Access expired", bad_signature_response.data["detail"])

        with patch("apps.certs.views.auditor_views.verify_session_token") as verify_session_token:
            verify_session_token.return_value = (str(row["grant_id"]), hash_token("wrong-secret"))
            mismatch_request = self.factory.get("/api/auditor/session-token/vessels/")
            mismatch_response = AuditorVesselListView.as_view()(mismatch_request, grant_token="session-token")

        self.assertEqual(mismatch_response.status_code, status.HTTP_410_GONE)
        repository.list_scoped_vessels.assert_not_called()
        repository.touch_last_accessed.assert_not_called()
        record_audit_event.assert_not_called()

    @patch("apps.certs.views.auditor_views.record_audit_event")
    @patch("apps.certs.views.auditor_views.repository")
    def test_expired_auditor_grant_and_scope_escape_do_not_disclose_cert_data(self, repository, record_audit_event) -> None:
        expired = grant_row(
            token_secret_hash=hash_token("session-secret"),
            expiry_at=timezone.now() - timedelta(minutes=1),
        )
        repository.get_grant.return_value = expired
        with patch("apps.certs.views.auditor_views.verify_session_token") as verify_session_token:
            verify_session_token.return_value = (str(expired["grant_id"]), hash_token("session-secret"))
            expired_request = self.factory.get("/api/auditor/session-token/cert/cert-1/")
            expired_response = AuditorCertDetailView.as_view()(
                expired_request,
                grant_token="session-token",
                cert_id=uuid.uuid4(),
            )

        self.assertEqual(expired_response.status_code, status.HTTP_410_GONE)
        repository.get_scoped_cert.assert_not_called()
        repository.touch_last_accessed.assert_not_called()

        active = grant_row(token_secret_hash=hash_token("session-secret"))
        repository.reset_mock()
        repository.get_grant.return_value = active
        repository.get_scoped_cert.return_value = None
        with patch("apps.certs.views.auditor_views.verify_session_token") as verify_session_token:
            verify_session_token.return_value = (str(active["grant_id"]), hash_token("session-secret"))
            escape_request = self.factory.get("/api/auditor/session-token/cert/out-of-scope/")
            escape_response = AuditorCertDetailView.as_view()(
                escape_request,
                grant_token="session-token",
                cert_id=uuid.uuid4(),
            )

        self.assertEqual(escape_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(escape_response.data["detail"], "Certificate not found in auditor scope.")
        repository.touch_last_accessed.assert_called_once_with(str(active["grant_id"]))
        record_audit_event.assert_not_called()

    @patch("apps.certs.views.auditor_views.record_audit_event")
    @patch("apps.certs.views.auditor_views.repository")
    def test_auditor_vessel_list_updates_last_accessed_only(self, repository, record_audit_event) -> None:
        row = grant_row(token_secret_hash=hash_token("session-secret"))
        repository.get_grant.return_value = row
        repository.list_scoped_vessels.return_value = [{"id": "vessel-a", "imo": "9876543", "name": "YC FORTITUDE"}]
        with patch("apps.certs.views.auditor_views.verify_session_token") as verify_session_token:
            verify_session_token.return_value = (str(row["grant_id"]), hash_token("session-secret"))
            request = self.factory.get("/api/auditor/session-token/vessels/")

            response = AuditorVesselListView.as_view()(request, grant_token="session-token")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repository.touch_last_accessed.assert_called_once_with(str(row["grant_id"]))
        record_audit_event.assert_not_called()

    @patch("apps.certs.views.auditor_views.record_audit_event")
    @patch("apps.certs.views.auditor_views.repository")
    def test_auditor_print_returns_audit_copy_watermark_without_audit_event(self, repository, record_audit_event) -> None:
        row = grant_row(token_secret_hash=hash_token("session-secret"))
        repository.get_grant.return_value = row
        with patch("apps.certs.views.auditor_views.verify_session_token") as verify_session_token:
            verify_session_token.return_value = (str(row["grant_id"]), hash_token("session-secret"))
            request = self.factory.post("/api/auditor/session-token/print/", {"trackedItemIds": []}, format="json")

            response = AuditorPrintView.as_view()(request, grant_token="session-token")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["watermarkApplied"], "AUDIT_COPY")
        self.assertIn("AUDIT COPY", response.data["watermarkText"])
        self.assertIn("ABS Auditor", response.data["watermarkText"])
        record_audit_event.assert_not_called()


if __name__ == "__main__":
    unittest.main()
