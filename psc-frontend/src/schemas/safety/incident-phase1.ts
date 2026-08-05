import { z } from 'zod';
import {
  safetyOptionalNullableStringSchema,
  safetyOptionalStringSchema,
} from './common';
import { safetyIncidentRiskBandSchema } from './incident';

export const SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION = 1 as const;
const phase1TriStateSchema = z.enum(['YES', 'NO', 'NA', '']).nullable().optional();

export const phase1LegacyEstimatedCostFields = [
  'cost_deviation',
  'cost_doctor_visits',
  'cost_evacuation',
  'cost_man_hours_lost',
  'cost_medicines_onboard',
  'cost_miscellaneous',
  'cost_off_hire',
  'cost_repatriation',
  'cost_vessel_delays',
  'miscellaneous_expenses_reason',
  'total_estimated_cost',
] as const;

export function stripPhase1EstimatedCostFields<
  T extends object | null | undefined,
>(injury: T): T {
  if (!injury) {
    return injury;
  }

  const nextInjury = { ...(injury as Record<string, unknown>) };
  phase1LegacyEstimatedCostFields.forEach((field) => {
    delete nextInjury[field];
  });
  return nextInjury as T;
}

export function phase1ExternalPartyInjuryPayload<
  T extends object | null | undefined,
>(injury: T): T | null {
  const strippedInjury = stripPhase1EstimatedCostFields(injury);
  if (!strippedInjury) {
    return null;
  }

  const currentInjury = Object.entries(
    strippedInjury as Record<string, unknown>
  ).reduce<Record<string, unknown>>((nextInjury, [field, value]) => {
    if (value === null || value === undefined) {
      return nextInjury;
    }
    nextInjury[field] = value;
    return nextInjury;
  }, {});

  if (
    currentInjury.injured_person_type !== 'CREW' &&
    currentInjury.injured_person_type !== 'NON_CREW'
  ) {
    currentInjury.injured_person_type = 'NON_CREW';
  }

  const hasCurrentDetails = Object.entries(currentInjury).some(
    ([field, value]) => {
      if (field === 'injured_person_type') {
        return false;
      }
      if (field === 'party_type' && (value === '' || value === 'PILOT')) {
        return false;
      }
      if (value === null || value === undefined) {
        return false;
      }
      if (typeof value === 'string') {
        return value.trim() !== '';
      }
      return true;
    }
  );

  return hasCurrentDetails ? (currentInjury as T) : null;
}

function parseOptionalDateTime(value?: string | null) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export const safetyExternalPartyInjurySchema = z
  .object({
    affected_body_areas: z.string().optional(),
    company_name: z.string().default(''),
    cost_deviation: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    cost_doctor_visits: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    cost_evacuation: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    cost_man_hours_lost: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    cost_medicines_onboard: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    cost_miscellaneous: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    cost_off_hire: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    cost_repatriation: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    cost_vessel_delays: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    crew_activity_type: z.string().optional(),
    crew_age: z
      .union([z.string(), z.coerce.number().int().nonnegative()])
      .nullable()
      .optional(),
    crew_rank: z.string().optional(),
    departure_date: z.string().nullable().optional(),
    first_aid_details: z.string().optional(),
    injured_person_type: z.enum(['CREW', 'NON_CREW']).default('NON_CREW'),
    last_port: z.string().optional(),
    miscellaneous_expenses_reason: z.string().optional(),
    nature_of_injury: z.string().optional(),
    notes: z.string().optional(),
    onboard_location: z.string().optional(),
    ocimf_fatality: z.boolean().nullable().optional(),
    ocimf_first_aid_case: z.boolean().nullable().optional(),
    ocimf_lost_workday_case: z.boolean().nullable().optional(),
    ocimf_medical_treatment_case: z.boolean().nullable().optional(),
    ocimf_permanent_partial_disability: z.boolean().nullable().optional(),
    ocimf_permanent_total_disability: z.boolean().nullable().optional(),
    ocimf_restricted_workday_case: z.boolean().nullable().optional(),
    party_name: z.string().default(''),
    party_type: z.union([
      z.literal(''),
      z.enum([
        'PILOT',
        'SHIPYARD',
        'STEVEDORE',
        'CONTRACTOR',
        'PASSENGER',
        'PORT_AGENT',
        'OTHER',
      ]),
    ]),
    prevention_action_taken_required: z.string().optional(),
    regulation_or_procedure_breach: z.string().optional(),
    risk_assessment_carried_out: z.enum(['YES', 'NO', 'NA', '']).optional(),
    severity: z.string().default(''),
    shore_assistance_required: z.boolean().nullable().optional(),
    source_of_injury: z.string().optional(),
    toolbox_meeting_carried_out: z.enum(['YES', 'NO', 'NA', '']).optional(),
    total_estimated_cost: z
      .union([z.string(), z.coerce.number()])
      .nullable()
      .optional(),
    vessel_condition: z.enum(['LOADED', 'BALLAST', '']).optional(),
    vessel_location: z.string().optional(),
    what_happened_narrative: z.string().optional(),
    why_it_happened_analysis: z.string().optional(),
  })
  .superRefine((values, ctx) => {
    if (values.injured_person_type !== 'NON_CREW') {
      return;
    }
    for (const field of [
      'party_name',
      'party_type',
      'company_name',
      'severity',
    ] as const) {
      if (!String(values[field] ?? '').trim()) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Required for non-crew injury.',
          path: [field],
        });
      }
    }
  });

export const safetyIncidentPhase1Schema = z.object({
  awaiting_daily_report_match: z.boolean().default(false),
  conflict_acknowledged: z.boolean().optional(),
  conflict_approver_role: z.enum(['MASTER', 'DPA']).optional(),
  external_party_injury: safetyExternalPartyInjurySchema.nullable().optional(),
  incident_type_id: z.coerce.number().int().positive().nullable().optional(),
  incident_type_other: z.string().max(128).nullable().optional(),
  latitude: z.coerce.number().nullable().optional(),
  longitude: z.coerce.number().nullable().optional(),
  shore_assistance_required: z.boolean().nullable().optional(),
  vessel_location: z.string().optional(),
  vessel_location_detail: z.string().max(128).nullable().optional(),
  onboard_location: z.string().optional(),
  last_port: z.string().optional(),
  departure_date: z.string().nullable().optional(),
  vessel_condition: z.enum(['LOADED', 'BALLAST', '']).optional(),
  risk_assessment_carried_out: phase1TriStateSchema,
  toolbox_meeting_carried_out: phase1TriStateSchema,
  permit_issued: phase1TriStateSchema,
  activity_type: z.string().max(128).nullable().optional(),
  loss_type_primary_id: z.coerce
    .number()
    .int()
    .positive()
    .nullable()
    .optional(),
  loss_type_secondary_id: z.coerce
    .number()
    .int()
    .positive()
    .nullable()
    .optional(),
  loss_type_tertiary_id: z.coerce
    .number()
    .int()
    .positive()
    .nullable()
    .optional(),
  loss_type_other: z
    .string()
    .max(256, 'Keep Other loss below 256 characters.')
    .nullable()
    .optional(),
  narrative: z.string().default(''),
  occurred_at: z.string().datetime({ offset: true }).nullable().optional(),
  office_notification_mode: z
    .enum(['ON_CALL', 'WHATSAPP', 'EMAIL'])
    .nullable()
    .optional(),
  office_notified: z.boolean().nullable().optional(),
  person_in_charge_id: safetyOptionalStringSchema,
  pic_candidate_id: safetyOptionalStringSchema,
  position_daily_report_id: safetyOptionalNullableStringSchema,
  position_source: safetyOptionalNullableStringSchema,
  weather_visibility_id: safetyOptionalNullableStringSchema,
  weather_precipitation_id: safetyOptionalNullableStringSchema,
  weather_sea_state_id: safetyOptionalNullableStringSchema,
  weather_wind_scale_id: safetyOptionalNullableStringSchema,
  weather_wind_direction_id: safetyOptionalNullableStringSchema,
  weather_lighting_source_id: safetyOptionalNullableStringSchema,
  weather_current_direction_id: safetyOptionalNullableStringSchema,
  weather_current_strength_knots: safetyOptionalNullableStringSchema,
  weather_ambient_temperature_c: safetyOptionalNullableStringSchema,
  weather_ice_condition_onboard_id: safetyOptionalNullableStringSchema,
  weather_ice_condition_at_sea_id: safetyOptionalNullableStringSchema,
  weather_light_condition_id: safetyOptionalNullableStringSchema,
  reported_at: z.string().datetime({ offset: true }).nullable().optional(),
  reporter_department: safetyOptionalStringSchema,
  reporter_device_fingerprint: z.string().default(''),
  reporter_email: z.string().email().optional().or(z.literal('')),
  reporter_name: z.string().default(''),
  reporter_rank: z.string().default(''),
  reporter_user_id: z.string().default(''),
  risk_band: safetyIncidentRiskBandSchema.nullable().optional(),
  schema_version: z.literal(SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION),
  vessel_code: safetyOptionalStringSchema,
  vessel_id: z.string().min(1),
});

export const safetyIncidentPhase1SubmitSchema = safetyIncidentPhase1Schema
  .extend({
    narrative: z
      .string()
      .trim()
      .min(200, 'Write more details. Minimum 200 characters.'),
    reporter_device_fingerprint: z
      .string()
      .min(1, 'Device ID missing. Refresh and try again.'),
    reporter_name: z.string().min(1, 'Enter reporter name.'),
    reporter_rank: z.string().min(1, 'Enter reporter rank.'),
    reporter_user_id: z.string().min(1, 'Reporter user ID is missing.'),
    risk_band: safetyIncidentRiskBandSchema,
  })
  .superRefine((values, ctx) => {
    const selectedLossTypes = [
      values.loss_type_primary_id,
      values.loss_type_secondary_id,
      values.loss_type_tertiary_id,
    ].filter((value): value is number => typeof value === 'number');
    const otherSelected =
      values.loss_type_other !== null && values.loss_type_other !== undefined;
    const totalLossTypes = selectedLossTypes.length + (otherSelected ? 1 : 0);

    if (new Set(selectedLossTypes).size !== selectedLossTypes.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Do not select the same loss type twice.',
        path: ['loss_type_primary_id'],
      });
    }

    if (totalLossTypes > 3) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Select up to 3 loss types only.',
        path: ['loss_type_primary_id'],
      });
    }

    if (otherSelected && !values.loss_type_other?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Write the other loss type.',
        path: ['loss_type_other'],
      });
    }

    if (
      values.office_notified === null ||
      values.office_notified === undefined
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Select if office was informed.',
        path: ['office_notified'],
      });
    }

    if (values.office_notified === true && !values.office_notification_mode) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Select how office was informed.',
        path: ['office_notification_mode'],
      });
    }

    const now = new Date();
    const occurredAt = parseOptionalDateTime(values.occurred_at);
    const reportedAt = parseOptionalDateTime(values.reported_at);

    if (occurredAt && occurredAt > now) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Incident time cannot be in the future.',
        path: ['occurred_at'],
      });
    }

    if (reportedAt && reportedAt > now) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Report time cannot be in the future.',
        path: ['reported_at'],
      });
    }

    if (occurredAt && reportedAt && occurredAt > reportedAt) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Incident time cannot be after report time.',
        path: ['occurred_at'],
      });
    }
  });

export type SafetyIncidentPhase1Values = z.infer<
  typeof safetyIncidentPhase1Schema
>;
export type SafetyIncidentPhase1SubmitValues = z.infer<
  typeof safetyIncidentPhase1SubmitSchema
>;
export type SafetyExternalPartyInjury = z.infer<
  typeof safetyExternalPartyInjurySchema
>;
