import { z } from "zod";

export const safetyCorrectiveActionStatusSchema = z.enum([
  "OPEN",
  "IN_PROGRESS",
  "PENDING_VERIFY",
  "CLOSED",
  "REOPENED",
]);

export const safetyPurchaseRequestSummarySchema = z.object({
  id: z.coerce.number().int().positive(),
  status: z.string().nullable(),
  is_archived: z.boolean().nullable(),
});

export const safetyCorrectiveActionSchema = z.object({
  id: z.coerce.number().int().positive(),
  title: z.string().min(1),
  description: z.string().min(1),
  assigned_crew_id: z.string().nullable().optional(),
  assigned_office_user_id: z.string().nullable().optional(),
  verifier_user_id: z.string().nullable().optional(),
  due_date: z.string().nullable().optional(),
  status: safetyCorrectiveActionStatusSchema,
  purchase_req_id: z.coerce.number().int().positive().nullable().optional(),
  purchase_request: safetyPurchaseRequestSummarySchema.nullable().optional(),
  physical_verification_done: z.boolean().default(false),
  aging_bucket: z.enum(["0-15", "15-30", "30-45", "45+"]),
  closed_at: z.string().nullable().optional(),
});

export type SafetyCorrectiveAction = z.infer<
  typeof safetyCorrectiveActionSchema
>;
