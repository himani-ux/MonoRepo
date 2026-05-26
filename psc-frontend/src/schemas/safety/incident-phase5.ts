import { z } from "zod";

import { safetySchemaVersionSchema } from "./common";
import { safetyIncidentFactSchema } from "./incident-phase4";

export const safetyIncidentCauseLayerSchema = z.enum([
  "IMMEDIATE",
  "INTERMEDIATE",
  "ROOT",
]);

export const safetyIncidentAnalysisToolSchema = z.enum([
  "STEP",
  "FACT_TREE",
  "ECF",
  "BARRIER",
  "CHANGE",
]);

export const safetyBiasGuardStateSchema = z.enum([
  "UNCHECKED",
  "PASSED",
  "WARNED",
  "BLOCKED",
  "OVERRIDE",
  "JUSTIFIED",
  "SOFTWARN_OVERRIDE",
]);

export const safetyIncidentCauseTagSchema = z.object({
  id: z.string().min(1).optional(),
  source_fact_id: z.string().min(1),
  mscat_subcode_id: z.string().min(1),
  mscat_category_id: z.coerce.number().int().positive().nullable().optional(),
  mscat_description: z.string().default(""),
  causal_layer: safetyIncidentCauseLayerSchema,
  analysis_tool: safetyIncidentAnalysisToolSchema,
  rationale: z.string().min(1),
});

export const safetyIncidentSafeguardFailureSchema = z.object({
  id: z.coerce.number().int().positive().optional(),
  safeguard_name: z.string().min(1),
  design_mscat_subcode_id: z.string().min(1),
  installation_mscat_subcode_id: z.string().min(1),
  maintenance_mscat_subcode_id: z.string().min(1),
  operation_mscat_subcode_id: z.string().min(1),
  testing_mscat_subcode_id: z.string().min(1),
  override_mscat_subcode_id: z.string().min(1),
  notes: z.string().default(""),
});

export const safetyIncidentBiasGuardSchema = z.object({
  guard_code: z.string().min(1),
  guard_name: z.string().min(1),
  family: z.string().min(1),
  bit_position: z.coerce.number().int().nonnegative(),
  acknowledged: z.boolean().default(false),
  evaluation_state: safetyBiasGuardStateSchema,
  justification: z.string().nullable().optional(),
});

export const safetyIncidentPhase5AssessmentSchema = z.object({
  people_contribution_text: z.string().default(""),
  process_gap_text: z.string().default(""),
  plant_failure_text: z.string().default(""),
  analysis_tools_used: z.array(safetyIncidentAnalysisToolSchema).default([]),
  human_factors_payload: z.record(z.any()).default({}),
  confirmation_override_reason: z.string().nullable().optional(),
  monocausal_justification: z.string().nullable().optional(),
});

export const safetyIncidentPhase5WorkspaceSchema = z.object({
  incident_id: z.string().min(1),
  investigation_depth: z.string().nullable().optional(),
  minimum_tools_required: z.coerce.number().int().positive(),
  analysis_tools_used: z.array(safetyIncidentAnalysisToolSchema).default([]),
  assessment: safetyIncidentPhase5AssessmentSchema.nullable().optional(),
  causes: z.array(safetyIncidentCauseTagSchema).default([]),
  safeguards: z.array(safetyIncidentSafeguardFailureSchema).default([]),
  bias_guards: z.array(safetyIncidentBiasGuardSchema).default([]),
  blame_evaluation: z.object({
    blocked: z.boolean().default(false),
    trigger_terms: z.array(z.string()).default([]),
    all_root_personal_factors: z.boolean().default(false),
    has_lack_of_control: z.boolean().default(false),
    override_by: z.string().nullable().optional(),
  }),
  matrix_rows: z
    .array(
      z.object({
        id: z.string().min(1),
        finding: z.string().default(""),
        pro_evidence: z.string().default(""),
        con_evidence: z.string().default(""),
        major_finding: z.boolean().default(false),
      }),
    )
    .default([]),
  facts: z.array(safetyIncidentFactSchema).default([]),
  schema_version: safetySchemaVersionSchema.default(1).optional(),
});

export type SafetyBiasGuard = z.infer<typeof safetyIncidentBiasGuardSchema>;
export type SafetyIncidentAnalysisTool = z.infer<typeof safetyIncidentAnalysisToolSchema>;
export type SafetyIncidentCauseTag = z.infer<typeof safetyIncidentCauseTagSchema>;
export type SafetyIncidentCauseLayer = z.infer<typeof safetyIncidentCauseLayerSchema>;
export type SafetyIncidentPhase5Assessment = z.infer<
  typeof safetyIncidentPhase5AssessmentSchema
>;
export type SafetyIncidentPhase5Workspace = z.infer<
  typeof safetyIncidentPhase5WorkspaceSchema
>;
export type SafetyIncidentSafeguardFailure = z.infer<
  typeof safetyIncidentSafeguardFailureSchema
>;
