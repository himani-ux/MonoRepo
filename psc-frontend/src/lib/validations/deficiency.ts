/**
 * Deficiency validation schemas
 *
 * Per VALIDATION_RULES.md Section 3 - Deficiency Validation
 * Uses Zod for type-safe validation with react-hook-form integration.
 */

import { z } from 'zod';

// ============================================================================
// Constants
// ============================================================================

/** Minimum characters for deficiency description */
const DESCRIPTION_MIN_LENGTH = 10;
/** Maximum characters for deficiency description */
const DESCRIPTION_MAX_LENGTH = 4000;

// ============================================================================
// Schema
// ============================================================================

/**
 * Add deficiency form schema.
 *
 * Per VALIDATION_RULES.md Section 3.1:
 * - def_code: Required, must be valid PSC def code
 * - def_text: Required, min 10 chars, max 4000 chars
 * - action_code: Optional, if provided must be valid
 * - target_date: Optional, must be today or future if provided
 */
export const addDeficiencySchema = z.object({
  // DefCode - required
  def_code: z
    .string({
      required_error: 'Deficiency code (DefCode) is required',
    })
    .min(1, 'Deficiency code (DefCode) is required'),

  // Description - required with length constraints
  def_text: z
    .string({
      required_error: 'Description is required',
    })
    .min(
      DESCRIPTION_MIN_LENGTH,
      `Description is required (${DESCRIPTION_MIN_LENGTH}-${DESCRIPTION_MAX_LENGTH} characters)`
    )
    .max(
      DESCRIPTION_MAX_LENGTH,
      `Description must be less than ${DESCRIPTION_MAX_LENGTH} characters`
    ),

  // Action code - required (drives follow-up tracking and closure)
  action_code: z
    .string({
      required_error: 'Action code is required',
    })
    .min(1, 'Action code is required'),

  // Target date - optional, must be today or future if provided
  target_date: z
    .string()
    .nullable()
    .optional()
    .refine(
      (val) => {
        if (!val) return true; // Optional, so null/undefined is OK
        const date = new Date(val);
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Start of today
        return date >= today;
      },
      {
        message: 'Target date must be today or in the future',
      }
    ),

  // Assigned crew member - optional, UUID of crew member responsible for this CAR
  assigned_crew_id: z
    .string()
    .nullable()
    .optional(),
});

/**
 * Inferred type from the add deficiency schema.
 */
export type AddDeficiencyFormData = z.infer<typeof addDeficiencySchema>;

// ============================================================================
// Default Values
// ============================================================================

/**
 * Default form values for adding a new deficiency.
 */
export const addDeficiencyDefaults: AddDeficiencyFormData = {
  def_code: '',
  def_text: '',
  action_code: '',
  target_date: null,
  assigned_crew_id: null,
};
