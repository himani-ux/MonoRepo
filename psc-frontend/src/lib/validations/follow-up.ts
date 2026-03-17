/**
 * PSC Follow-up wizard validation schemas.
 *
 * Uses Zod for type-safe validation with react-hook-form integration.
 */

import { z } from 'zod';

// ============================================================================
// Deficiency Update Schema (Step 3)
// ============================================================================

export const deficiencyUpdateSchema = z.object({
  deficiency_id: z.string(),
  action_code_id: z.number({
    required_error: 'Action code is required',
    invalid_type_error: 'Action code must be a number',
  }),
  notes: z.string().optional().default(''),
});

export type DeficiencyUpdateFormData = z.infer<typeof deficiencyUpdateSchema>;

// ============================================================================
// Step 3 — Action Code Updates + Reinspection Date
// ============================================================================

export const followUpStep3Schema = z.object({
  reinspection_date: z
    .string({ required_error: 'Reinspection date is required' })
    .refine(
      (val) => {
        if (!val) return false;
        const date = new Date(val);
        const today = new Date();
        today.setHours(23, 59, 59, 999);
        return date <= today;
      },
      { message: 'Reinspection date cannot be in the future' },
    ),
  deficiency_updates: z
    .array(deficiencyUpdateSchema)
    .min(1, 'At least one deficiency update is required'),
});

export type FollowUpStep3Data = z.infer<typeof followUpStep3Schema>;

// ============================================================================
// Step 4 — Optional Report Upload
// ============================================================================

export const followUpStep4Schema = z
  .object({
    report_file: z.instanceof(File).nullable().optional(),
    report_description: z.string().optional().default(''),
  })
  .refine(
    (data) => {
      if (data.report_file && !data.report_description?.trim()) {
        return false;
      }
      return true;
    },
    { message: 'Description is required when uploading a report', path: ['report_description'] },
  );

export type FollowUpStep4Data = z.infer<typeof followUpStep4Schema>;

// ============================================================================
// Combined wizard data (all steps — used by follow-up-wizard.tsx and route)
// ============================================================================

export interface FollowUpFormData {
  reinspection_date: string;
  notes: string;
  deficiency_updates: DeficiencyUpdateFormData[];
  report_file?: File | null;
  report_description?: string;
}

// ============================================================================
// Follow-up simple form schema (used by follow-up-form.tsx)
// ============================================================================

export const followUpFormSchema = z.object({
  inspection_date: z
    .string({ required_error: 'Follow-up date is required' })
    .min(1, 'Follow-up date is required'),
  port_place: z
    .string({ required_error: 'Port/Place is required' })
    .min(1, 'Port/Place is required'),
  country: z.string().optional().default(''),
  authority: z.string().optional().default(''),
  deficiency_updates: z
    .array(
      z.object({
        deficiency_id: z.number(),
        action_code_id: z.number(),
      }),
    )
    .optional()
    .default([]),
});

export type FollowUpSimpleFormData = z.infer<typeof followUpFormSchema>;

export const followUpFormDefaults: FollowUpSimpleFormData = {
  inspection_date: '',
  port_place: '',
  country: '',
  authority: '',
  deficiency_updates: [],
};
