from __future__ import annotations

import datetime as dt
import os
import unittest
from unittest.mock import MagicMock, patch
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.core.management import call_command

from apps.certs.services.iws_age_gate import (
    IWS_CANONICAL_CODE,
    IwsAgeGateRepository,
    VesselAgeGateInput,
    recompute_iws_age_gate,
    set_iws_manual_override,
)


class CertIwsAgeGateTests(unittest.TestCase):
    def test_recompute_disables_overage_vessel_and_writes_audit(self) -> None:
        catalog_id = str(uuid.uuid4())
        vessel_id = str(uuid.uuid4())
        repository = MagicMock()
        repository.get_iws_catalog_row.return_value = {
            "catalog_id": catalog_id,
            "canonical_code": IWS_CANONICAL_CODE,
            "age_gate_max_years": 15,
        }
        repository.list_vessel_age_inputs.return_value = [
            VesselAgeGateInput(vessel_id=vessel_id, year_built=2010, stored_age=None),
        ]
        repository.get_vessel_config.return_value = {
            "vessel_id": vessel_id,
            "iws_age_gate_disabled": False,
            "iws_manual_override_enabled": False,
        }
        repository.upsert_vessel_config.return_value = {
            "vessel_id": vessel_id,
            "iws_age_gate_disabled": True,
            "iws_age_gate_disabled_reason": "vessel_age_exceeds_gate",
            "iws_age_gate_last_age_years": 16,
            "iws_manual_override_enabled": False,
        }

        result = recompute_iws_age_gate(
            repository=repository,
            actor_id="recompute_iws_age_gate",
            today=dt.date(2026, 6, 25),
        )

        self.assertEqual(result.evaluated_count, 1)
        self.assertEqual(result.disabled_count, 1)
        self.assertEqual(result.override_preserved_count, 0)
        update_payload = repository.upsert_vessel_config.call_args.kwargs["values"]
        self.assertTrue(update_payload["iws_age_gate_disabled"])
        self.assertEqual(update_payload["iws_age_gate_last_age_years"], 16)
        repository.record_age_gate_audit.assert_called_once()
        self.assertEqual(repository.record_age_gate_audit.call_args.kwargs["after"]["iws_age_gate_disabled"], True)

    def test_recompute_preserves_manual_override_for_overage_vessel(self) -> None:
        catalog_id = str(uuid.uuid4())
        vessel_id = str(uuid.uuid4())
        repository = MagicMock()
        repository.get_iws_catalog_row.return_value = {
            "catalog_id": catalog_id,
            "canonical_code": IWS_CANONICAL_CODE,
            "age_gate_max_years": 15,
        }
        repository.list_vessel_age_inputs.return_value = [
            VesselAgeGateInput(vessel_id=vessel_id, year_built=2009, stored_age=None),
        ]
        repository.get_vessel_config.return_value = {
            "vessel_id": vessel_id,
            "iws_age_gate_disabled": False,
            "iws_manual_override_enabled": True,
            "iws_manual_override_reason": "Existing IWS enrollment accepted by DPA.",
        }
        repository.upsert_vessel_config.return_value = {
            "vessel_id": vessel_id,
            "iws_age_gate_disabled": False,
            "iws_age_gate_last_age_years": 17,
            "iws_manual_override_enabled": True,
        }

        result = recompute_iws_age_gate(
            repository=repository,
            actor_id="recompute_iws_age_gate",
            today=dt.date(2026, 6, 25),
        )

        self.assertEqual(result.evaluated_count, 1)
        self.assertEqual(result.disabled_count, 0)
        self.assertEqual(result.override_preserved_count, 1)
        update_payload = repository.upsert_vessel_config.call_args.kwargs["values"]
        self.assertFalse(update_payload["iws_age_gate_disabled"])
        self.assertIsNone(update_payload["iws_age_gate_disabled_reason"])
        repository.record_age_gate_audit.assert_not_called()

    def test_recompute_skips_vessels_without_certs_config(self) -> None:
        repository = MagicMock()
        repository.get_iws_catalog_row.return_value = {
            "catalog_id": str(uuid.uuid4()),
            "canonical_code": IWS_CANONICAL_CODE,
            "age_gate_max_years": 15,
        }
        repository.list_vessel_age_inputs.return_value = [
            VesselAgeGateInput(vessel_id=str(uuid.uuid4()), year_built=2009, stored_age=None),
        ]
        repository.get_vessel_config.return_value = None

        result = recompute_iws_age_gate(
            repository=repository,
            actor_id="recompute_iws_age_gate",
            today=dt.date(2026, 6, 25),
        )

        self.assertEqual(result.evaluated_count, 1)
        self.assertEqual(result.skipped_count, 1)
        repository.upsert_vessel_config.assert_not_called()
        repository.record_age_gate_audit.assert_not_called()

    def test_manual_override_requires_reason_when_enabled(self) -> None:
        with self.assertRaises(ValueError):
            set_iws_manual_override(
                vessel_id=str(uuid.uuid4()),
                enabled=True,
                reason=" ",
                actor_id="dpa-1",
                repository=MagicMock(),
            )

    def test_manual_override_updates_vessel_config_and_audits(self) -> None:
        catalog_id = str(uuid.uuid4())
        vessel_id = str(uuid.uuid4())
        repository = MagicMock()
        repository.get_iws_catalog_row.return_value = {"catalog_id": catalog_id, "age_gate_max_years": 15}
        repository.get_vessel_config.return_value = {
            "vessel_id": vessel_id,
            "iws_manual_override_enabled": False,
            "iws_age_gate_disabled": True,
        }
        repository.upsert_vessel_config.return_value = {
            "vessel_id": vessel_id,
            "iws_manual_override_enabled": True,
            "iws_manual_override_reason": "Older vessel remains IWS enrolled.",
            "iws_age_gate_disabled": False,
        }

        set_iws_manual_override(
            vessel_id=vessel_id,
            enabled=True,
            reason="Older vessel remains IWS enrolled.",
            actor_id="dpa-1",
            repository=repository,
        )

        update_payload = repository.upsert_vessel_config.call_args.kwargs["values"]
        self.assertTrue(update_payload["iws_manual_override_enabled"])
        self.assertFalse(update_payload["iws_age_gate_disabled"])
        repository.record_age_gate_audit.assert_called_once()
        self.assertEqual(repository.record_age_gate_audit.call_args.kwargs["actor_id"], "dpa-1")

    @patch("apps.certs.services.iws_age_gate.connection")
    def test_repository_reads_yearbuilt_and_age_without_sibling_module_calls(self, connection) -> None:
        cursor = MagicMock()
        cursor.description = [("vessel_id",), ("year_built",), ("stored_age",)]
        cursor.fetchall.return_value = [(uuid.uuid4(), 2010, 16)]
        connection.cursor.return_value.__enter__.return_value = cursor

        vessels = IwsAgeGateRepository().list_vessel_age_inputs()

        self.assertEqual(len(vessels), 1)
        sql = cursor.execute.call_args.args[0]
        self.assertIn("dbo.VesselData", sql)
        self.assertIn("YearBuilt", sql)
        self.assertIn("Age", sql)

    def test_management_command_uses_recompute_service(self) -> None:
        with patch("apps.certs.management.commands.recompute_iws_age_gate.recompute_iws_age_gate") as recompute:
            recompute.return_value.evaluated_count = 2
            recompute.return_value.disabled_count = 1
            recompute.return_value.enabled_count = 0
            recompute.return_value.override_preserved_count = 1
            recompute.return_value.skipped_count = 0

            call_command("recompute_iws_age_gate")

        recompute.assert_called_once()
