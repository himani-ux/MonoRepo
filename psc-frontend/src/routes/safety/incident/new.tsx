import { useNavigate } from "react-router-dom";

import { SafetyIncidentPhase1Form } from "../../../components/safety/incident/phase1-form";
import { useToast } from "../../../hooks/use-toast";
import {
  safetyApi,
  type SafetyIncidentCreatePayload,
  type SafetyIncidentPhase1SubmitPayload,
} from "../../../lib/api/safety";
import type { SafetyIncidentPhase1SubmitValues } from "../../../schemas/safety/incident-phase1";

export default function SafetyIncidentCreatePage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  async function handleSubmitPhase(values: SafetyIncidentPhase1SubmitValues) {
    try {
      const createPayload: SafetyIncidentCreatePayload = {
        awaiting_daily_report_match: values.awaiting_daily_report_match,
        external_party_injury: values.external_party_injury ?? null,
        first_hour_checklist_done: values.first_hour_checklist_done,
        incident_type_id: values.incident_type_id ?? null,
        latitude: values.latitude,
        longitude: values.longitude,
        loss_type_primary_id: values.loss_type_primary_id ?? null,
        narrative: values.narrative,
        occurred_at: values.occurred_at ?? null,
        pic_candidate_id: values.pic_candidate_id,
        position_daily_report_id: values.position_daily_report_id ?? null,
        position_source: values.position_source ?? null,
        reported_at: values.reported_at ?? null,
        reporter_department: values.reporter_department,
        reporter_device_fingerprint: values.reporter_device_fingerprint,
        reporter_name: values.reporter_name,
        reporter_rank: values.reporter_rank,
        reporter_user_id: values.reporter_user_id,
        schema_version: values.schema_version,
        vessel_code: values.vessel_code,
        vessel_id: values.vessel_id,
      };
      const incident = await safetyApi.createIncident(createPayload);
      const submitPayload: SafetyIncidentPhase1SubmitPayload = {
        conflict_acknowledged: values.conflict_acknowledged,
        conflict_approver_role: values.conflict_approver_role,
        person_in_charge_id: values.person_in_charge_id,
        pic_candidate_id: values.pic_candidate_id,
      };
      const submitted = await safetyApi.submitIncidentPhase1(incident.id, submitPayload);
      toast({
        title: "Phase 1 submitted",
        description: submitted.phase_2_handoff?.message ?? "Incident advanced to Phase 2.",
        variant: "success",
      });
      navigate(`/safety/incidents/${incident.public_id ?? incident.id}/phase-2`, {
        state: {
          phase2Handoff: submitted.phase_2_handoff,
        },
      });
    } catch (error) {
      toast({
        title: "Unable to continue",
        description:
          error instanceof Error
            ? error.message
            : "Incident phase 1 could not be saved.",
        variant: "destructive",
      });
    }
  }

  return <SafetyIncidentPhase1Form mode="create" onSubmitPhase={handleSubmitPhase} />;
}
