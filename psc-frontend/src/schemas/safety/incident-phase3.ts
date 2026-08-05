import { z } from "zod";

import { safetySchemaVersionSchema } from "./common";

export const safetyIncidentPhase3TabCodeSchema = z.enum([
  "POSITION",
  "PEOPLE",
  "PARTS",
  "PAPER",
  "ELECTRONIC",
]);

export const safetyIncidentPhase3TabSchema = z.object({
  id: z.string().optional(),
  tab_code: safetyIncidentPhase3TabCodeSchema,
  summary: z.string().default(""),
  entry_count: z.coerce.number().int().nonnegative().default(0),
  structured_data: z.record(z.string(), z.unknown()).default({}),
  status_chip: z.string().default(""),
  na_justification: z.string().nullable().optional(),
});

export const safetyChainOfCustodyRowSchema = z.object({
  id: z.string().optional(),
  description: z.string().default(""),
  collection_timestamp: z.string().default(""),
  collector_name: z.string().default(""),
  collector_signature: z.string().default(""),
  storage_location: z.string().default(""),
  witness_signature: z.string().default(""),
  current_holder: z.string().default(""),
  handover_log: z
    .array(
      z.object({
        handover_timestamp: z.string(),
        handover_from: z.string(),
        handover_to: z.string(),
      }),
    )
    .default([]),
});

export const safetyEvidenceMatrixRowSchema = z.object({
  id: z.string().optional(),
  finding: z.string().default(""),
  pro_evidence: z.string().default(""),
  con_evidence: z.string().default(""),
  source_label: z.string().default(""),
  comments: z.string().default(""),
});

export const safetyEvidenceDeadlineTaskSchema = z.object({
  id: z.string().optional(),
  task_code: z.string().default(""),
  title: z.string().default("Evidence task"),
  due_at: z.string().default(""),
  due_within: z.string().or(z.number()).optional(),
  severity: z.enum(["INFO", "ALERT", "HARD_ALARM"]).default("INFO"),
  status: z.enum(["PENDING", "COMPLETED", "OVERDUE"]).default("PENDING"),
  completed_at: z.string().nullable().optional(),
  justification: z.string().nullable().optional(),
});

export const safetyWitnessInterviewSchema = z.object({
  id: z.string().optional(),
  witness_name: z.string().default("Unnamed witness"),
  interview_type: z.enum(["FORMAL", "INFORMAL"]).default("INFORMAL"),
  reason_formal_impossible: z.string().nullable().optional(),
  make_acquaintance_notes: z.string().default(""),
  introduction_notes: z.string().default(""),
  meeting_notes: z.string().default(""),
  conclusion_notes: z.string().default(""),
  question_rows: z.array(z.record(z.string(), z.unknown())).default([]),
  read_back_confirmed: z.boolean().default(false),
  witness_signature: z.string().nullable().optional(),
  copy_to_witness_recorded: z.boolean().default(false),
  is_final: z.boolean().default(false),
  phase_count: z.coerce.number().int().nonnegative().default(0),
});

export const safetyIncidentPhase3WorkspaceSchema = z.object({
  position: safetyIncidentPhase3TabSchema,
  people: safetyIncidentPhase3TabSchema,
  parts: safetyIncidentPhase3TabSchema,
  paper: safetyIncidentPhase3TabSchema,
  electronic: safetyIncidentPhase3TabSchema,
  chain_of_custody: z.array(safetyChainOfCustodyRowSchema).default([]),
  evidence_matrix: z.array(safetyEvidenceMatrixRowSchema).default([]),
  deadline_tasks: z.array(safetyEvidenceDeadlineTaskSchema).default([]),
  interviews: z.array(safetyWitnessInterviewSchema).default([]),
  schema_version: safetySchemaVersionSchema.default(1).optional(),
});

export type SafetyChainOfCustodyRow = z.infer<typeof safetyChainOfCustodyRowSchema>;
export type SafetyEvidenceDeadlineTask = z.infer<typeof safetyEvidenceDeadlineTaskSchema>;
export type SafetyEvidenceMatrixRow = z.infer<typeof safetyEvidenceMatrixRowSchema>;
export type SafetyIncidentPhase3Tab = z.infer<typeof safetyIncidentPhase3TabSchema>;
export type SafetyIncidentPhase3Workspace = z.infer<typeof safetyIncidentPhase3WorkspaceSchema>;
export type SafetyWitnessInterview = z.infer<typeof safetyWitnessInterviewSchema>;
