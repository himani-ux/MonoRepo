/**
 * Evidence upload validation schemas
 *
 * Per VALIDATION_RULES.md Section 6 - Evidence Validation
 * Uses Zod for type-safe validation with react-hook-form integration.
 */

import { z } from 'zod';
import { EVIDENCE_TYPES } from '@/lib/utils/constants';

// ============================================================================
// Constants
// ============================================================================

/** Maximum file size in bytes (3MB) */
export const MAX_FILE_SIZE = 3 * 1024 * 1024;

/** Allowed MIME types */
export const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/jpg',
] as const;

/** Allowed file extensions display string */
export const ALLOWED_EXTENSIONS = 'PDF, JPG, JPEG';

/** Minimum description length */
const DESCRIPTION_MIN_LENGTH = 5;

/** Maximum description length */
const DESCRIPTION_MAX_LENGTH = 500;

// ============================================================================
// Evidence Type Options
// ============================================================================

/** Evidence type options for the select dropdown */
export const EVIDENCE_TYPE_OPTIONS = [
  { value: EVIDENCE_TYPES.BEFORE, label: 'Before' },
  { value: EVIDENCE_TYPES.AFTER, label: 'After' },
  { value: EVIDENCE_TYPES.EVIDENCE, label: 'Evidence' },
  { value: EVIDENCE_TYPES.OTHER, label: 'Other' },
] as const;

// ============================================================================
// Schema
// ============================================================================

/**
 * Evidence upload form schema.
 *
 * Per VALIDATION_RULES.md Section 6.1:
 * - evidence_type: Required, must be BEFORE/AFTER/EVIDENCE/OTHER
 * - description: Required, 5-500 chars
 * - File validated separately (not part of Zod schema due to File type)
 */
export const evidenceSchema = z.object({
  evidence_type: z.enum(
    [
      EVIDENCE_TYPES.BEFORE,
      EVIDENCE_TYPES.AFTER,
      EVIDENCE_TYPES.EVIDENCE,
      EVIDENCE_TYPES.OTHER,
    ],
    {
      errorMap: () => ({ message: 'Evidence type is required' }),
    }
  ),

  description: z
    .string({
      required_error: 'Evidence description is required',
    })
    .min(
      DESCRIPTION_MIN_LENGTH,
      `Description is required (${DESCRIPTION_MIN_LENGTH}-${DESCRIPTION_MAX_LENGTH} characters)`
    )
    .max(
      DESCRIPTION_MAX_LENGTH,
      `Description must be less than ${DESCRIPTION_MAX_LENGTH} characters`
    ),
});

/**
 * Inferred type from the evidence schema.
 */
export type EvidenceFormData = z.infer<typeof evidenceSchema>;

// ============================================================================
// File Validation Helper
// ============================================================================

/**
 * Validate an evidence file.
 * Returns null if valid, or an error message string.
 */
export function validateEvidenceFile(file: File): string | null {
  if (file.size > MAX_FILE_SIZE) {
    return 'File size must not exceed 3MB';
  }
  if (!ALLOWED_FILE_TYPES.includes(file.type as (typeof ALLOWED_FILE_TYPES)[number])) {
    return 'Only PDF and JPG/JPEG files are allowed';
  }
  return null;
}

// ============================================================================
// Default Values
// ============================================================================

/**
 * Default form values for uploading evidence.
 */
export const evidenceDefaults: EvidenceFormData = {
  evidence_type: EVIDENCE_TYPES.BEFORE,
  description: '',
};
