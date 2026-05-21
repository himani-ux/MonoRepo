import { z } from "zod";

import { safetySchemaVersionSchema } from "./common";

export const safetyIncidentFactConfidenceSchema = z.enum(["LOW", "MEDIUM", "HIGH"]);

export const safetyIncidentFactSchema = z.object({
  id: z.coerce.number().int().positive().optional(),
  sequence_index: z.coerce.number().int().positive(),
  fact_text: z.string().min(1),
  fact_timestamp: z.string().nullable().optional(),
  source_evidence_id: z.coerce.number().int().positive(),
  evidence_summary: z.string().default("Evidence link"),
  confidence: safetyIncidentFactConfidenceSchema.default("MEDIUM"),
  contradicts_fact: z.coerce.number().int().positive().nullable().optional(),
  hindsight_guard_triggered: z.boolean().default(false),
  hindsight_override_reason: z.string().nullable().optional(),
});

export const safetyDuplicateCandidateSchema = z.object({
  incident_id: z.coerce.number().int().positive(),
  vessel_code: z.string().nullable().optional(),
  vessel_display_name: z.string().nullable().optional(),
  vessel_id: z.string(),
  vessel_name: z.string().nullable().optional(),
  distance_nm: z.coerce.number().nonnegative(),
  overlap_hours: z.coerce.number().nonnegative(),
  narrative_overlap: z.coerce.number().min(0).max(1),
});

export const safetyIncidentPhase4WorkspaceSchema = z.object({
  facts: z.array(safetyIncidentFactSchema).default([]),
  duplicates: z.array(safetyDuplicateCandidateSchema).default([]),
  schema_version: safetySchemaVersionSchema.default(1).optional(),
});

export type SafetyDuplicateCandidate = z.infer<typeof safetyDuplicateCandidateSchema>;
export type SafetyIncidentFact = z.infer<typeof safetyIncidentFactSchema>;
export type SafetyIncidentPhase4Workspace = z.infer<typeof safetyIncidentPhase4WorkspaceSchema>;
