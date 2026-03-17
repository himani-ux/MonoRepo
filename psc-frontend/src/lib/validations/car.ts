/**
 * CAR validation schemas
 *
 * Per VALIDATION_RULES.md Sections 4 & 5 — CAR and Corrective Action Validation
 * Uses Zod for type-safe validation with react-hook-form integration.
 */

import { z } from 'zod';
import { ROOT_CAUSE_MIN_LENGTH } from '@/lib/utils/constants';
import type { CorrectiveAction, Evidence } from '@/types';

// ============================================================================
// Constants
// ============================================================================

const CUSTOM_CAUSE_MAX_LENGTH = 500;
const ACTION_DESCRIPTION_MIN = 10;
const ACTION_DESCRIPTION_MAX = 4000;
const ACTION_DESCRIPTION_MIN_FOR_SUBMIT = 50;

// ============================================================================
// Update CAR Schema (Save Draft — partial validation)
// ============================================================================

/**
 * Schema for saving a CAR draft.
 *
 * Per VALIDATION_RULES.md Section 4.1:
 * - root_cause_summary: Optional, but min 50 chars if provided
 * - target_date: Optional, today or future if provided
 * - clc_item_ids: Optional array of CLC codes
 * - custom_cause_text: Optional, max 500 chars
 */
export const updateCarSchema = z.object({
  root_cause_summary: z
    .string()
    .optional()
    .refine(
      (val) => !val || val.length === 0 || val.length >= ROOT_CAUSE_MIN_LENGTH,
      {
        message: `Root cause summary must be at least ${ROOT_CAUSE_MIN_LENGTH} characters`,
      }
    ),

  target_date: z
    .string()
    .nullable()
    .optional()
    .refine(
      (val) => {
        if (!val) return true;
        const date = new Date(val);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return date >= today;
      },
      { message: 'Target date must be today or in the future' }
    ),

  clc_item_ids: z.array(z.string()).optional(),

  custom_cause_text: z
    .string()
    .max(CUSTOM_CAUSE_MAX_LENGTH, `Custom cause text must be less than ${CUSTOM_CAUSE_MAX_LENGTH} characters`)
    .optional()
    .or(z.literal('')),
});

export type UpdateCarFormData = z.infer<typeof updateCarSchema>;

export const updateCarDefaults: UpdateCarFormData = {
  root_cause_summary: '',
  target_date: null,
  clc_item_ids: [],
  custom_cause_text: '',
};

// ============================================================================
// Add Corrective Action Schema
// ============================================================================

/**
 * Schema for adding a corrective action.
 *
 * Per VALIDATION_RULES.md Section 5.1:
 * - action_type: Required, IMMEDIATE or LONG_TERM
 * - description: Required, 10-4000 chars
 * - owner_crew_id: Optional
 * - due_date: Optional, today or future if provided
 */
export const addActionSchema = z.object({
  action_type: z.enum(['IMMEDIATE', 'LONG_TERM'], {
    required_error: 'Action type is required',
  }),

  description: z
    .string({ required_error: 'Description is required' })
    .min(
      ACTION_DESCRIPTION_MIN,
      `Description is required (${ACTION_DESCRIPTION_MIN}-${ACTION_DESCRIPTION_MAX} characters)`
    )
    .max(
      ACTION_DESCRIPTION_MAX,
      `Description must be less than ${ACTION_DESCRIPTION_MAX} characters`
    ),

  owner_crew_id: z.string().nullable().optional(),

  due_date: z
    .string()
    .nullable()
    .optional()
    .refine(
      (val) => {
        if (!val) return true;
        const date = new Date(val);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return date >= today;
      },
      { message: 'Due date must be today or in the future' }
    ),
});

export type AddActionFormData = z.infer<typeof addActionSchema>;

export const addActionDefaults: AddActionFormData = {
  action_type: 'IMMEDIATE',
  description: '',
  owner_crew_id: null,
  due_date: null,
};

// ============================================================================
// Submit CAR Validation (all preconditions)
// ============================================================================

export interface SubmitValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Validate all preconditions for CAR submission.
 *
 * Per VALIDATION_RULES.md Section 4.2:
 * - root_cause_summary >= 50 characters
 * - At least 1 CLC code OR custom_cause_text
 * - At least 1 IMMEDIATE corrective action
 * - At least 1 LONG_TERM corrective action
 * - At least 1 BEFORE evidence
 * - At least 1 AFTER evidence
 */
export function validateCarSubmission(
  rootCauseSummary: string | null | undefined,
  clcItemIds: string[],
  customCauseText: string | null | undefined,
  actions: CorrectiveAction[],
  evidence: Evidence[]
): SubmitValidationResult {
  const errors: string[] = [];

  // Root cause summary (trim to prevent whitespace-padding bypass)
  if (!rootCauseSummary || rootCauseSummary.trim().length < ROOT_CAUSE_MIN_LENGTH) {
    errors.push(
      `Root cause summary must be at least ${ROOT_CAUSE_MIN_LENGTH} characters`
    );
  }

  // At least one root cause (CLC or custom)
  if (clcItemIds.length === 0 && (!customCauseText || customCauseText.trim().length === 0)) {
    errors.push('At least one root cause is required (CLC code or custom cause)');
  }

  // Corrective actions
  const immediateActions = actions.filter((a) => a.action_type === 'IMMEDIATE');
  const longTermActions = actions.filter((a) => a.action_type === 'LONG_TERM');

  if (immediateActions.length === 0) {
    errors.push('At least one immediate corrective action is required');
  }

  if (longTermActions.length === 0) {
    errors.push('At least one long-term corrective action is required');
  }

  // Action description quality (at least one per category with >= 50 trimmed chars)
  if (immediateActions.length > 0) {
    const hasSubstantive = immediateActions.some(
      (a) => (a.description || '').trim().length >= ACTION_DESCRIPTION_MIN_FOR_SUBMIT
    );
    if (!hasSubstantive) {
      errors.push(
        `At least one immediate action must have a description of ${ACTION_DESCRIPTION_MIN_FOR_SUBMIT}+ characters`
      );
    }
  }
  if (longTermActions.length > 0) {
    const hasSubstantive = longTermActions.some(
      (a) => (a.description || '').trim().length >= ACTION_DESCRIPTION_MIN_FOR_SUBMIT
    );
    if (!hasSubstantive) {
      errors.push(
        `At least one long-term action must have a description of ${ACTION_DESCRIPTION_MIN_FOR_SUBMIT}+ characters`
      );
    }
  }

  // Evidence
  const beforeEvidence = evidence.filter((e) => e.evidence_type === 'BEFORE');
  const afterEvidence = evidence.filter((e) => e.evidence_type === 'AFTER');

  if (beforeEvidence.length === 0) {
    errors.push('At least one BEFORE evidence is required');
  }

  if (afterEvidence.length === 0) {
    errors.push('At least one AFTER evidence is required');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
