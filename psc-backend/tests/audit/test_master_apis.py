from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.inspection.audit.serializers.masters import (
    ExternalAuditOrgSerializer,
    QualifiedAuditorSerializer,
    VesselRoDelegationSerializer,
)
from apps.inspection.audit.views.masters import ExternalAuditOrgListCreateView


class AuditMasterApiContractTests(unittest.TestCase):
    def test_master_api_requires_authentication_and_process_gate(self):
        factory = APIRequestFactory()
        view = ExternalAuditOrgListCreateView.as_view()

        unauthenticated = view(factory.get("/api/audit/masters/external-audit-orgs/"))
        self.assertEqual(unauthenticated.status_code, 401)

        request = factory.get("/api/audit/masters/external-audit-orgs/")
        user = SimpleNamespace(
            is_authenticated=True,
            id="master-1",
            role="MASTER",
            process_ids=[],
        )
        force_authenticate(request, user=user)
        denied = view(request)
        self.assertEqual(denied.status_code, 403)

    def test_master_routes_are_registered(self):
        self.assertEqual(resolve("/api/audit/masters/qualified-auditors/").url_name, "audit-master-qualified-auditors")
        self.assertEqual(resolve("/api/audit/masters/external-audit-orgs/").url_name, "audit-master-external-audit-orgs")
        self.assertEqual(resolve("/api/audit/masters/ro-delegations/").url_name, "audit-master-ro-delegations")

    def test_external_org_serializer_normalizes_type(self):
        serializer = ExternalAuditOrgSerializer(
            data={"name": "ABS", "org_type": "ro", "is_active": True}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["org_type"], "RO")

    def test_qualified_auditor_rejects_reversed_qualification_dates(self):
        serializer = QualifiedAuditorSerializer(
            data={
                "user_id": "KSM0001",
                "qualification_text": "ISM auditor",
                "qualification_date": date(2026, 8, 19),
                "expiry_date": date(2026, 8, 18),
                "scope_standards_csv": "ISM",
                "auditor_scope": "INTERNAL",
                "qualified_for_seq": True,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("expiry_date", serializer.errors)

    @patch("apps.inspection.audit.serializers.masters.MasterExternalAuditOrg.objects")
    def test_ro_delegation_requires_active_external_organisation(self, objects):
        objects.filter.return_value.exists.return_value = False
        serializer = VesselRoDelegationSerializer(
            data={
                "target_vessel_id": "11111111-1111-1111-1111-111111111111",
                "standard_code": "ISM",
                "master_external_audit_org_id": "22222222-2222-2222-2222-222222222222",
                "effective_from": date(2026, 8, 19),
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("master_external_audit_org_id", serializer.errors)

    @patch("apps.inspection.audit.serializers.masters.MasterExternalAuditOrg.objects")
    @patch("apps.inspection.audit.serializers.masters.VesselAuditRoDelegation.objects")
    def test_ro_delegation_rejects_overlapping_window(self, delegation_objects, org_objects):
        org_objects.filter.return_value.exists.return_value = True
        delegation_objects.filter.return_value.exclude.return_value.filter.return_value.exists.return_value = True
        serializer = VesselRoDelegationSerializer(
            data={
                "target_vessel_id": "11111111-1111-1111-1111-111111111111",
                "standard_code": "ism",
                "master_external_audit_org_id": "22222222-2222-2222-2222-222222222222",
                "effective_from": date(2026, 8, 19),
                "effective_to": date(2026, 9, 19),
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(any("already covers" in str(error) for error in serializer.errors["non_field_errors"]))


if __name__ == "__main__":
    unittest.main()
