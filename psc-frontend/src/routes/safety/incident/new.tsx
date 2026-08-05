import { useNavigate } from 'react-router-dom';

import { SafetyIncidentPhase1Form } from '../../../components/safety/incident/phase1-form';
import { useToast } from '../../../hooks/use-toast';
import { getErrorMessage } from '../../../lib/api/client';
import {
  safetyApi,
  type SafetyIncidentCreatePayload,
  type SafetyIncidentPhase1SubmitPayload,
  type SafetyIncidentPhase2Payload,
} from '../../../lib/api/safety';
import {
  phase1ExternalPartyInjuryPayload,
  type SafetyIncidentPhase1SubmitValues,
} from '../../../schemas/safety/incident-phase1';

function deriveInvestigationDepth(
  riskBand: SafetyIncidentPhase1SubmitValues['risk_band']
) {
  if (riskBand === 'RED') {
    return 'DEEP' as const;
  }
  if (riskBand === 'YELLOW') {
    return 'MEDIUM' as const;
  }
  return 'SHALLOW' as const;
}

export default function SafetyIncidentCreatePage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  async function handleSubmitPhase(values: SafetyIncidentPhase1SubmitValues) {
    try {
      const createPayload: SafetyIncidentCreatePayload = {
        awaiting_daily_report_match: values.awaiting_daily_report_match,
        external_party_injury: phase1ExternalPartyInjuryPayload(
          values.external_party_injury ?? null
        ),
        incident_type_id: values.incident_type_id ?? null,
        latitude: values.latitude,
        longitude: values.longitude,
        shore_assistance_required: values.shore_assistance_required ?? null,
        vessel_location: values.vessel_location?.trim() || '',
        vessel_location_detail: values.vessel_location_detail?.trim() || null,
        onboard_location: values.onboard_location?.trim() || '',
        last_port: values.last_port?.trim() || '',
        departure_date: values.departure_date ?? null,
        vessel_condition: values.vessel_condition || null,
        loss_type_primary_id: values.loss_type_primary_id ?? null,
        loss_type_secondary_id: values.loss_type_secondary_id ?? null,
        loss_type_tertiary_id: values.loss_type_tertiary_id ?? null,
        loss_type_other: values.loss_type_other?.trim() || null,
        activity_type: values.activity_type?.trim() || null,
        narrative: values.narrative,
        occurred_at: values.occurred_at ?? null,
        office_notification_mode: values.office_notification_mode ?? null,
        office_notified: values.office_notified ?? null,
        pic_candidate_id: values.pic_candidate_id,
        position_daily_report_id: values.position_daily_report_id ?? null,
        position_source: values.position_source ?? null,
        reported_at: values.reported_at ?? null,
        reporter_department: values.reporter_department,
        reporter_device_fingerprint: values.reporter_device_fingerprint,
        reporter_name: values.reporter_name,
        reporter_rank: values.reporter_rank,
        reporter_user_id: values.reporter_user_id,
        permit_issued: values.permit_issued || null,
        risk_assessment_carried_out: values.risk_assessment_carried_out || null,
        risk_band: values.risk_band,
        schema_version: values.schema_version,
        vessel_code: values.vessel_code,
        vessel_id: values.vessel_id,
        toolbox_meeting_carried_out: values.toolbox_meeting_carried_out || null,
        weather_ambient_temperature_c:
          values.weather_ambient_temperature_c?.trim() || null,
        weather_current_direction_id:
          values.weather_current_direction_id ?? null,
        weather_current_strength_knots:
          values.weather_current_strength_knots?.trim() || null,
        weather_ice_condition_at_sea_id:
          values.weather_ice_condition_at_sea_id ?? null,
        weather_ice_condition_onboard_id:
          values.weather_ice_condition_onboard_id ?? null,
        weather_light_condition_id: values.weather_light_condition_id ?? null,
        weather_lighting_source_id: values.weather_lighting_source_id ?? null,
        weather_precipitation_id: values.weather_precipitation_id ?? null,
        weather_sea_state_id: values.weather_sea_state_id ?? null,
        weather_visibility_id: values.weather_visibility_id ?? null,
        weather_wind_direction_id: values.weather_wind_direction_id ?? null,
        weather_wind_scale_id: values.weather_wind_scale_id ?? null,
      };
      const incident = await safetyApi.createIncident(createPayload);
      const submitPayload: SafetyIncidentPhase1SubmitPayload = {
        conflict_acknowledged: values.conflict_acknowledged,
        conflict_approver_role: values.conflict_approver_role,
        person_in_charge_id: values.person_in_charge_id,
        pic_candidate_id: values.pic_candidate_id,
      };
      const submitted = await safetyApi.submitIncidentPhase1(
        incident.id,
        submitPayload
      );
      if (submitted.phase_2_handoff?.can_edit_phase_2) {
        const phase2Payload: SafetyIncidentPhase2Payload = {
          imo_classifier: 'NOT_APPLICABLE',
          investigation_depth: deriveInvestigationDepth(values.risk_band),
          loss_type_primary_id: values.loss_type_primary_id ?? null,
          loss_type_secondary_id: values.loss_type_secondary_id ?? null,
          loss_type_tertiary_id: values.loss_type_tertiary_id ?? null,
          loss_type_other: values.loss_type_other?.trim() || null,
          office_notification_mode: values.office_notification_mode ?? null,
          office_notified: values.office_notified ?? null,
          risk_band: values.risk_band,
          schema_version: 1,
        };
        await safetyApi.updateIncidentPhase2(incident.id, phase2Payload);
        const phase2Submitted = await safetyApi.submitIncidentPhase2(
          incident.id
        );
        toast({
          title: 'Report submitted',
          description: `Incident ${phase2Submitted.incident_number ?? incident.id} is ready for next step.`,
          variant: 'success',
        });
        navigate(`/safety/incidents/${incident.id}/phase-2`);
        return;
      }

      toast({
        title: 'Report submitted',
        description:
          submitted.phase_2_handoff?.message ??
          'Office needs to confirm communication next.',
        variant: 'success',
      });
      navigate(`/safety/incidents/${incident.id}/office-communication`, {
        state: {
          phase2Handoff: submitted.phase_2_handoff,
        },
      });
    } catch (error) {
      toast({
        title: 'Cannot continue',
        description: getErrorMessage(error) || 'Report could not be saved.',
        variant: 'destructive',
      });
    }
  }

  return (
    <SafetyIncidentPhase1Form mode="create" onSubmitPhase={handleSubmitPhase} />
  );
}
