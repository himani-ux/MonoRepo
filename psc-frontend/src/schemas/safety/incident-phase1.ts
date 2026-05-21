import { z } from "zod";
import {
  safetyOptionalNullableStringSchema,
  safetyOptionalStringSchema,
} from "./common";

export const SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION = 1 as const;

export const safetyExternalPartyInjurySchema = z.object({
  company_name: z.string().default(""),
  notes: z.string().optional(),
  party_name: z.string().default(""),
  party_type: z.enum([
    "PILOT",
    "SHIPYARD",
    "STEVEDORE",
    "CONTRACTOR",
    "PASSENGER",
    "PORT_AGENT",
    "OTHER",
  ]),
  severity: z.string().default(""),
});

export const safetyIncidentPhase1Schema = z.object({
  awaiting_daily_report_match: z.boolean().default(false),
  conflict_acknowledged: z.boolean().optional(),
  conflict_approver_role: z.enum(["MASTER", "DPA"]).optional(),
  external_party_injury: safetyExternalPartyInjurySchema.nullable().optional(),
  first_hour_checklist_done: z.boolean().default(false),
  incident_type_id: z.coerce.number().int().positive().nullable().optional(),
  latitude: z.coerce.number().nullable().optional(),
  longitude: z.coerce.number().nullable().optional(),
  loss_type_primary_id: z.coerce.number().int().positive().nullable().optional(),
  narrative: z.string().default(""),
  occurred_at: z.string().datetime({ offset: true }).nullable().optional(),
  person_in_charge_id: safetyOptionalStringSchema,
  pic_candidate_id: safetyOptionalStringSchema,
  position_daily_report_id: safetyOptionalNullableStringSchema,
  position_source: safetyOptionalNullableStringSchema,
  reported_at: z.string().datetime({ offset: true }).nullable().optional(),
  reporter_department: safetyOptionalStringSchema,
  reporter_device_fingerprint: z.string().default(""),
  reporter_email: z.string().email().optional().or(z.literal("")),
  reporter_name: z.string().default(""),
  reporter_rank: z.string().default(""),
  reporter_user_id: z.string().default(""),
  schema_version: z.literal(SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION),
  vessel_code: safetyOptionalStringSchema,
  vessel_id: z.string().min(1),
});

export const safetyIncidentPhase1SubmitSchema = safetyIncidentPhase1Schema.extend({
  first_hour_checklist_done: z.literal(true),
  narrative: z.string().trim().min(200, "Incident narrative must be at least 200 characters."),
  reporter_device_fingerprint: z.string().min(1, "Reporter signature device data was not captured. Refresh and try again."),
  reporter_name: z.string().min(1, "Reporter typed name is required."),
  reporter_rank: z.string().min(1, "Reporter rank is required."),
  reporter_user_id: z.string().min(1, "Reporter identity is required."),
});

export type SafetyIncidentPhase1Values = z.infer<typeof safetyIncidentPhase1Schema>;
export type SafetyIncidentPhase1SubmitValues = z.infer<typeof safetyIncidentPhase1SubmitSchema>;
export type SafetyExternalPartyInjury = z.infer<typeof safetyExternalPartyInjurySchema>;
