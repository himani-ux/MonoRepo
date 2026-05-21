import { z } from "zod";

import {
  safetySchemaVersionSchema,
  safetyVesselIdSchema,
} from "./common";

export const SAFETY_INCIDENT_SCHEMA_VERSION = 1;

export const safetyIncidentRecordTypeSchema = z.enum(["INCIDENT", "NEAR_MISS"]);
export const safetyIncidentRiskBandSchema = z.enum(["GREEN", "YELLOW", "RED"]);
export const safetyIncidentImoClassifierSchema = z.enum([
  "SMC",
  "MC",
  "MI",
  "NOT_APPLICABLE",
]);
export const safetyIncidentDepthSchema = z.enum(["SHALLOW", "MEDIUM", "DEEP"]);

export const safetyIncidentSchema = z.object({
  current_phase: z.coerce.number().int().min(0).max(9).default(1),
  draft_reference: z.string().min(1).nullable().default(null),
  dpa_notified_at: z.string().datetime({ offset: true }).nullable().optional(),
  fm_notified_at: z.string().datetime({ offset: true }).nullable().optional(),
  id: z.coerce.number().int().positive().optional(),
  imo_classifier: safetyIncidentImoClassifierSchema.nullable().optional(),
  incident_number: z.string().min(1),
  incident_type_id: z.coerce.number().int().positive().nullable().optional(),
  investigation_depth: safetyIncidentDepthSchema.nullable().optional(),
  loss_type_primary_id: z.coerce.number().int().positive().nullable().optional(),
  narrative: z.string().nullable().optional(),
  notification_channel_count: z.coerce.number().int().nonnegative().optional(),
  occurred_at: z.string().datetime({ offset: true }).nullable().optional(),
  office_notified_at: z.string().datetime({ offset: true }).nullable().optional(),
  pic_user_id: z.string().min(1).nullable().optional(),
  record_type: safetyIncidentRecordTypeSchema.default("INCIDENT"),
  reported_at: z.string().datetime({ offset: true }).nullable().optional(),
  resources_allocated: z.string().nullable().optional(),
  risk_band: safetyIncidentRiskBandSchema.nullable().optional(),
  schema_version: safetySchemaVersionSchema.default(SAFETY_INCIDENT_SCHEMA_VERSION),
  state: z.string().min(1),
  vessel_code: z.string().min(1).optional(),
  vessel_id: safetyVesselIdSchema,
});

export const safetyIncidentFiltersSchema = z.object({
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  risk_band: safetyIncidentRiskBandSchema.optional(),
  state: z.string().optional(),
  vessel_id: safetyVesselIdSchema.optional(),
});

export type SafetyIncident = z.infer<typeof safetyIncidentSchema>;
export type SafetyIncidentFilters = z.infer<typeof safetyIncidentFiltersSchema>;
