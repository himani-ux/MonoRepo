import { z } from "zod";

import { safetyIncidentRiskBandSchema } from "./incident";
import { safetySchemaVersionSchema } from "./common";

export const SAFETY_INCIDENT_PHASE_6_SCHEMA_VERSION = 1;

export const safetyRecommendationTierSchema = z.enum([
  "CORRECTIVE",
  "PREVENTIVE",
  "LESSONS_LEARNT",
]);

export const safetyRecommendationThemeSchema = z.object({
  code: z.string().min(1),
  label: z.string().min(1),
});

export const safetyCorrectiveActionSchema = z.object({
  id: z.string().min(1).optional(),
  title: z.string().min(1),
  description: z.string().min(1),
  assigned_crew_id: z.string().nullable().optional(),
  assigned_office_user_id: z.string().nullable().optional(),
  verifier_user_id: z.string().nullable().optional(),
  due_date: z.string().nullable().optional(),
  status: z.string().min(1),
  purchase_req_id: z.coerce.number().int().positive().nullable().optional(),
});

export const safetyRecommendationSchema = z.object({
  id: z.string().min(1).optional(),
  tier: safetyRecommendationTierSchema,
  theme_code: z.string().nullable().optional(),
  title: z.string().min(1),
  description: z.string().min(1),
  rationale: z.string().nullable().optional(),
  estimated_effort: z.string().nullable().optional(),
  estimated_likelihood_reduction: z
    .enum(["LOW", "MED", "HIGH"])
    .nullable()
    .optional(),
  residual_risk_statement: z.string().nullable().optional(),
  alarp_attested: z.boolean().default(false),
  tolerable_failure_filter: z.boolean().default(false),
  linked_ca_ids: z.string().nullable().optional(),
  corrective_actions: z.array(safetyCorrectiveActionSchema).default([]),
});

export const safetyIncidentPhase6WorkspaceSchema = z.object({
  incident_id: z.string().min(1),
  threshold_hint: z.string().nullable().optional(),
  themes: z.array(safetyRecommendationThemeSchema).default([]),
  tier_counts: z.record(z.coerce.number().int().nonnegative()).default({}),
  missing_tiers: z.array(safetyRecommendationTierSchema).default([]),
  alarp_complete: z.boolean().default(false),
  bias_guards_complete: z.boolean().default(false),
  blame_evaluation: z
    .object({
      blocked: z.boolean().default(false),
      trigger_terms: z.array(z.string()).default([]),
      all_root_personal_factors: z.boolean().default(false),
      has_lack_of_control: z.boolean().default(false),
      override_by: z.string().nullable().optional(),
    })
    .default({
      blocked: false,
      trigger_terms: [],
      all_root_personal_factors: false,
      has_lack_of_control: false,
      override_by: null,
    }),
  gate_blockers: z.array(z.string()).default([]),
  tolerable_failure_allowed: z.boolean().default(false),
  recommendations: z.object({
    CORRECTIVE: z.array(safetyRecommendationSchema).default([]),
    PREVENTIVE: z.array(safetyRecommendationSchema).default([]),
    LESSONS_LEARNT: z.array(safetyRecommendationSchema).default([]),
  }),
  corrective_actions: z.array(safetyCorrectiveActionSchema).default([]),
  risk_band: safetyIncidentRiskBandSchema.optional(),
  schema_version: safetySchemaVersionSchema.default(
    SAFETY_INCIDENT_PHASE_6_SCHEMA_VERSION,
  ),
});

export type SafetyCorrectiveAction = z.infer<
  typeof safetyCorrectiveActionSchema
>;
export type SafetyIncidentPhase6Workspace = z.infer<
  typeof safetyIncidentPhase6WorkspaceSchema
>;
export type SafetyRecommendation = z.infer<typeof safetyRecommendationSchema>;
export type SafetyRecommendationTheme = z.infer<
  typeof safetyRecommendationThemeSchema
>;
