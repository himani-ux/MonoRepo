import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import IncidentPhaseSwitcher from '../../../../components/safety/incident/incident-phase-switcher';
import { SafetyIncidentPhase1Form } from '../../../../components/safety/incident/phase1-form';
import { useToast } from '../../../../hooks/use-toast';
import {
  safetyApi,
  type SafetyIncidentCreatePayload,
  type SafetyIncidentPhase1Record,
} from '../../../../lib/api/safety';
import {
  phase1ExternalPartyInjuryPayload,
  type SafetyIncidentPhase1SubmitValues,
  type SafetyIncidentPhase1Values,
} from '../../../../schemas/safety/incident-phase1';

function toNumberOrNull(value: unknown): number | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function toStringOrNull(value: unknown): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  const text = String(value);
  return text ? text : null;
}

function toStringOrEmpty(value: unknown): string {
  return toStringOrNull(value) ?? '';
}

function mapRecordToInitialValues(
  record: SafetyIncidentPhase1Record
): Partial<SafetyIncidentPhase1Values> {
  return {
    awaiting_daily_report_match: Boolean(record.awaiting_daily_report_match),
    external_party_injury: (record.external_party_injury ??
      null) as SafetyIncidentPhase1Values['external_party_injury'],
    incident_type_id: toNumberOrNull(record.incident_type_id),
    latitude: toNumberOrNull(record.latitude),
    longitude: toNumberOrNull(record.longitude),
    shore_assistance_required: record.shore_assistance_required ?? null,
    vessel_location: toStringOrEmpty(record.vessel_location),
    vessel_location_detail: toStringOrEmpty(record.vessel_location_detail),
    onboard_location: toStringOrEmpty(record.onboard_location),
    last_port: toStringOrEmpty(record.last_port),
    departure_date: record.departure_date ?? null,
    vessel_condition: record.vessel_condition ?? '',
    loss_type_other: record.loss_type_other ?? null,
    loss_type_primary_id: toNumberOrNull(record.loss_type_primary_id),
    loss_type_secondary_id: toNumberOrNull(record.loss_type_secondary_id),
    loss_type_tertiary_id: toNumberOrNull(record.loss_type_tertiary_id),
    activity_type: toStringOrEmpty(record.activity_type),
    narrative: toStringOrEmpty(record.narrative),
    occurred_at: record.occurred_at ?? null,
    office_notification_mode: record.office_notification_mode ?? null,
    office_notified: record.office_notified ?? null,
    position_daily_report_id: record.position_daily_report_id ?? null,
    position_source: record.position_source ?? null,
    reported_at: record.reported_at ?? null,
    reporter_department: toStringOrEmpty(record.reporter_department),
    reporter_device_fingerprint: toStringOrEmpty(
      record.reporter_device_fingerprint
    ),
    reporter_name: toStringOrEmpty(record.reporter_name),
    reporter_rank: toStringOrEmpty(record.reporter_rank),
    reporter_user_id: toStringOrEmpty(record.reporter_user_id),
    permit_issued: record.permit_issued ?? null,
    risk_assessment_carried_out: record.risk_assessment_carried_out ?? null,
    risk_band: record.risk_band ?? null,
    schema_version: 1,
    vessel_code: toStringOrEmpty(record.vessel_code),
    vessel_id: toStringOrEmpty(record.vessel_id),
    toolbox_meeting_carried_out: record.toolbox_meeting_carried_out ?? null,
    weather_ambient_temperature_c: record.weather_ambient_temperature_c ?? null,
    weather_current_direction_id: record.weather_current_direction_id ?? null,
    weather_current_strength_knots:
      record.weather_current_strength_knots ?? null,
    weather_ice_condition_at_sea_id:
      record.weather_ice_condition_at_sea_id ?? null,
    weather_ice_condition_onboard_id:
      record.weather_ice_condition_onboard_id ?? null,
    weather_light_condition_id: record.weather_light_condition_id ?? null,
    weather_lighting_source_id: record.weather_lighting_source_id ?? null,
    weather_precipitation_id: record.weather_precipitation_id ?? null,
    weather_sea_state_id: record.weather_sea_state_id ?? null,
    weather_visibility_id: record.weather_visibility_id ?? null,
    weather_wind_direction_id: record.weather_wind_direction_id ?? null,
    weather_wind_scale_id: record.weather_wind_scale_id ?? null,
  };
}

function buildPhase1UpdatePayload(
  values: SafetyIncidentPhase1Values | SafetyIncidentPhase1SubmitValues
): SafetyIncidentCreatePayload {
  const payload: SafetyIncidentCreatePayload = {
    awaiting_daily_report_match: values.awaiting_daily_report_match,
    incident_type_id: values.incident_type_id ?? null,
    latitude: values.latitude ?? null,
    longitude: values.longitude ?? null,
    shore_assistance_required: values.shore_assistance_required ?? null,
    vessel_location: values.vessel_location?.trim() || '',
    vessel_location_detail: values.vessel_location_detail?.trim() || null,
    onboard_location: values.onboard_location?.trim() || '',
    last_port: values.last_port?.trim() || '',
    departure_date: values.departure_date ?? null,
    vessel_condition: values.vessel_condition || null,
    loss_type_other: values.loss_type_other?.trim() || null,
    loss_type_primary_id: values.loss_type_primary_id ?? null,
    loss_type_secondary_id: values.loss_type_secondary_id ?? null,
    loss_type_tertiary_id: values.loss_type_tertiary_id ?? null,
    activity_type: values.activity_type?.trim() || null,
    narrative: values.narrative,
    occurred_at: values.occurred_at ?? null,
    office_notification_mode: values.office_notification_mode ?? null,
    office_notified: values.office_notified ?? null,
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
    risk_band: values.risk_band ?? undefined,
    schema_version: values.schema_version,
    vessel_code: values.vessel_code,
    vessel_id: values.vessel_id,
    toolbox_meeting_carried_out: values.toolbox_meeting_carried_out || null,
    weather_ambient_temperature_c:
      values.weather_ambient_temperature_c?.trim() || null,
    weather_current_direction_id: values.weather_current_direction_id ?? null,
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

  if (values.external_party_injury) {
    payload.external_party_injury = phase1ExternalPartyInjuryPayload(
      values.external_party_injury
    ) as Record<string, unknown>;
  }

  return payload;
}

export default function SafetyIncidentPhase1Route() {
  const { id } = useParams();
  const { toast } = useToast();
  const [initialValues, setInitialValues] =
    useState<Partial<SafetyIncidentPhase1Values>>();
  const [isLoading, setIsLoading] = useState(Boolean(id));

  useEffect(() => {
    if (!id) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;

    async function loadPhase1() {
      try {
        const phase1 = await safetyApi.getIncidentPhase1(id);
        if (!cancelled) {
          setInitialValues(mapRecordToInitialValues(phase1));
        }
      } catch (error) {
        if (!cancelled) {
          toast({
            title: 'Unable to load incident',
            description:
              error instanceof Error
                ? error.message
                : 'Incident Phase 1 details could not be loaded.',
            variant: 'destructive',
          });
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadPhase1();
    return () => {
      cancelled = true;
    };
  }, [id, toast]);

  async function handleSavePhase1(
    values: SafetyIncidentPhase1Values | SafetyIncidentPhase1SubmitValues
  ) {
    if (!id) {
      return;
    }

    await safetyApi.updateIncidentPhase1(id, buildPhase1UpdatePayload(values));
  }

  if (isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-600">
          Loading incident Phase 1 details...
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <IncidentPhaseSwitcher activePhase={1} />
      <SafetyIncidentPhase1Form
        incidentId={id ?? 'draft'}
        initialValues={initialValues}
        mode="edit"
        onSaveDraft={handleSavePhase1}
        onSubmitPhase={handleSavePhase1}
      />
    </section>
  );
}
