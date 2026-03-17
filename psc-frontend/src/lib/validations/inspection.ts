/**
 * Inspection validation schemas
 *
 * Per VALIDATION_RULES.md Section 2 - Inspection Validation
 * Uses Zod for type-safe validation with react-hook-form integration.
 */

import { z } from 'zod';
import {
  INSPECTION_TYPES,
  PSC_SUBTYPES,
  MAX_FILE_SIZE_BYTES,
  ALLOWED_FILE_TYPES,
} from '@/lib/utils/constants';

// ============================================================================
// Constants
// ============================================================================

/** Minimum characters for port field */
const PORT_MIN_LENGTH = 2;
/** Maximum characters for port field */
const PORT_MAX_LENGTH = 200;
/** Maximum characters for country field */
const COUNTRY_MAX_LENGTH = 100;
/** Maximum characters for authority field */
const AUTHORITY_MAX_LENGTH = 200;
/** Maximum characters for inspector name field */
const INSPECTOR_NAME_MAX_LENGTH = 200;
/** Maximum characters for report reference field */
const REPORT_REFERENCE_MAX_LENGTH = 100;
/** Maximum characters for detention reason */
const DETENTION_REASON_MAX_LENGTH = 500;

// ============================================================================
// Base Schema
// ============================================================================

/**
 * Create inspection form schema.
 *
 * This validates the form fields for creating a new inspection.
 * The vessel_id is not included as it comes from the auth context for vessel users.
 */
export const createInspectionSchema = z
  .object({
    // Type - required
    inspection_type: z.enum(
      [INSPECTION_TYPES.PSC, INSPECTION_TYPES.RS, INSPECTION_TYPES.AUDIT],
      {
        required_error: 'Inspection type is required',
        invalid_type_error: 'Invalid inspection type',
      }
    ),

    // PSC Subtype - conditionally required
    psc_subtype: z
      .enum(
        [
          PSC_SUBTYPES.INITIAL,
          PSC_SUBTYPES.EXPANDED,
          PSC_SUBTYPES.CIC,
          PSC_SUBTYPES.FOLLOW_UP,
        ],
        {
          invalid_type_error: 'Invalid PSC subtype',
        }
      )
      .nullable()
      .optional(),

    // Date - required, not future
    inspection_date: z
      .string({
        required_error: 'Inspection date is required',
      })
      .refine(
        (val) => {
          if (!val) return false;
          const date = new Date(val);
          const today = new Date();
          today.setHours(23, 59, 59, 999); // End of today
          return date <= today;
        },
        {
          message: 'Inspection date cannot be in the future',
        }
      ),

    // Port - required
    port: z
      .string({
        required_error: 'Port/Place is required',
      })
      .min(PORT_MIN_LENGTH, `Port/Place is required (${PORT_MIN_LENGTH}-${PORT_MAX_LENGTH} characters)`)
      .max(PORT_MAX_LENGTH, `Port/Place must be less than ${PORT_MAX_LENGTH} characters`),

    // Country/Port State - optional
    port_state: z
      .string()
      .max(COUNTRY_MAX_LENGTH, `Country must be less than ${COUNTRY_MAX_LENGTH} characters`)
      .optional()
      .default(''),

    // MOU - conditionally required for PSC
    mou_code: z.string().nullable().optional(),

    // Authority - optional
    authority: z
      .string()
      .max(AUTHORITY_MAX_LENGTH, `Authority must be less than ${AUTHORITY_MAX_LENGTH} characters`)
      .optional()
      .default(''),

    // Inspector name - optional
    inspector_name: z
      .string()
      .max(
        INSPECTOR_NAME_MAX_LENGTH,
        `Inspector name must be less than ${INSPECTOR_NAME_MAX_LENGTH} characters`
      )
      .nullable()
      .optional(),

    // Report reference - optional
    report_reference: z
      .string()
      .max(
        REPORT_REFERENCE_MAX_LENGTH,
        `Report reference must be less than ${REPORT_REFERENCE_MAX_LENGTH} characters`
      )
      .optional()
      .default(''),

    // Detention flag
    is_detention: z.boolean().default(false),

    // Deficiencies reported flag
    def_reported: z.enum(['YES', 'NO'], {
      required_error: 'Please indicate if deficiencies were reported',
    }),

    // Detention reason - conditionally required when is_detention is true
    detention_reason: z
      .string()
      .max(
        DETENTION_REASON_MAX_LENGTH,
        `Detention reason must be less than ${DETENTION_REASON_MAX_LENGTH} characters`
      )
      .nullable()
      .optional(),
  })
  .refine(
    (data) => {
      // PSC subtype is required when inspection_type is PSC
      if (data.inspection_type === INSPECTION_TYPES.PSC) {
        return !!data.psc_subtype;
      }
      return true;
    },
    {
      message: 'PSC subtype is required for PSC inspections',
      path: ['psc_subtype'],
    }
  )
  .refine(
    (data) => {
      // MOU is required when inspection_type is PSC
      if (data.inspection_type === INSPECTION_TYPES.PSC) {
        return !!data.mou_code;
      }
      return true;
    },
    {
      message: 'MOU is required for PSC inspections',
      path: ['mou_code'],
    }
  );

/**
 * Inferred type from the create inspection schema.
 */
export type CreateInspectionFormData = z.infer<typeof createInspectionSchema>;

// ============================================================================
// File Validation
// ============================================================================

/**
 * Validate inspection report file.
 *
 * Per VALIDATION_RULES.md:
 * - PDF, JPG, JPEG only
 * - Max 3MB
 */
export function validateInspectionReportFile(file: File): {
  valid: boolean;
  error?: string;
} {
  // Check file type
  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: 'Only PDF, JPG, and JPEG files are allowed',
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return {
      valid: false,
      error: 'File size must be less than 3MB',
    };
  }

  return { valid: true };
}

// ============================================================================
// Submit Validation
// ============================================================================

/**
 * Validation rules for submitting an inspection.
 *
 * Per VALIDATION_RULES.md Section 2.2:
 * - Status must be DRAFT
 * - At least 1 report file attached
 * - All deficiencies have valid def_code
 */
export interface InspectionSubmitValidation {
  hasReport: boolean;
  allDeficienciesValid: boolean;
}

/**
 * Check if an inspection can be submitted.
 */
export function canSubmitInspection(validation: InspectionSubmitValidation): {
  canSubmit: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!validation.hasReport) {
    errors.push('Inspection report must be attached before submission');
  }

  if (!validation.allDeficienciesValid) {
    errors.push('All deficiencies must have a deficiency code');
  }

  return {
    canSubmit: errors.length === 0,
    errors,
  };
}

// ============================================================================
// Default Values
// ============================================================================

/**
 * Default form values for creating a new inspection.
 */
export const createInspectionDefaults: Partial<CreateInspectionFormData> = {
  inspection_type: undefined,
  psc_subtype: null,
  inspection_date: new Date().toISOString().split('T')[0], // Today's date
  port: '',
  port_state: '',
  mou_code: null,
  authority: '',
  inspector_name: null,
  report_reference: '',
  is_detention: false,
  def_reported: undefined as unknown as 'YES' | 'NO',
  detention_reason: null,
};
