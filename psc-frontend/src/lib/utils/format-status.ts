import type { BadgeProps } from '@/components/ui';
import type { InspectionStatus, OperationalStatus, CARStatus, DefStatus } from '@/types';

export type StatusType = InspectionStatus | OperationalStatus | CARStatus | DefStatus | 'OVERDUE' | 'DETENTION';

const enumAcronyms = new Set([
  'CAR',
  'CE',
  'CO',
  'DOC',
  'DPA',
  'EMS',
  'HOD',
  'IMO',
  'ISM',
  'ISPS',
  'KSM',
  'MLC',
  'NC',
  'OBS',
  'OFI',
  'OPM',
  'PIC',
  'PSC',
  'RCA',
  'SEQ',
  'SMC',
  'SMS',
]);

const enumLowercaseWords = new Set(['and', 'at', 'by', 'for', 'in', 'of', 'on', 'or', 'to', 'with']);

const enumLabelMap: Record<string, string> = {
  CERT_VALID: 'Certificate Valid',
  CLASS_SOCIETY: 'Class Society',
  DPA_CLOSED: 'Closed',
  EXTERNAL_CLOSE_OUT_LETTER: 'External Close-Out Letter',
  FISHBONE_ISHIKAWA: 'Fishbone / Ishikawa',
  FIVE_WHY: '5 Why',
  N_A: 'N/A',
  NA: 'N/A',
  OFFICE_DEPT: 'Office Department',
  PENDING_EXTERNAL_CLOSE: 'Pending External Close',
  RENEWAL_AT_RISK: 'Renewal at Risk',
};

const statusVariantMap: Record<string, BadgeProps['variant']> = {
  // Inspection statuses (legacy)
  DRAFT: 'draft',
  SUBMITTED: 'submitted',
  PIC_REVIEWED: 'pic_reviewed',
  OVERDUE: 'overdue',
  DETENTION: 'detention',
  // Operational status (computed)
  OPEN: 'submitted',
  // CAR unified workflow statuses
  ALLOTTED: 'draft',
  IN_PROGRESS: 'submitted',
  PENDING_CE_REVIEW: 'warning',
  PENDING_MASTER_REVIEW: 'warning',
  SUBMITTED_TO_PIC: 'submitted',
  PIC_REVIEW: 'pic_accepted',
  SUBMITTED_TO_DPA: 'info',
  CLOSED: 'dpa_closed',
  RETURNED_FOR_REWORK: 'rework_requested',
  // DEF workflow statuses (legacy)
  ALLOCATED: 'draft',
  COMPLETED: 'info',
  UNDER_REVIEW: 'warning',
  APPROVED: 'success',
};

const statusLabelMap: Record<string, string> = {
  // Inspection statuses (legacy)
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  PIC_REVIEWED: 'PIC Reviewed',
  OVERDUE: 'Overdue',
  DETENTION: 'Detention',
  // Operational status (computed)
  OPEN: 'Open',
  // CAR unified workflow statuses
  ALLOTTED: 'Allotted',
  IN_PROGRESS: 'In Progress',
  PENDING_CE_REVIEW: 'Pending CE Review',
  PENDING_MASTER_REVIEW: 'Pending Master Review',
  SUBMITTED_TO_PIC: 'Submitted to PIC',
  PIC_REVIEW: 'PIC Review',
  SUBMITTED_TO_DPA: 'Submitted to DPA',
  CLOSED: 'Closed',
  RETURNED_FOR_REWORK: 'Rework',
  // DEF workflow statuses (legacy)
  ALLOCATED: 'Allocated',
  COMPLETED: 'Completed',
  UNDER_REVIEW: 'Under Review',
  APPROVED: 'Approved',
  // Inspection close status (aliased)
  DPA_CLOSED: 'Closed',
};

/**
 * Utility function to get badge variant for a status
 */
export function getStatusVariant(status: StatusType | string | null | undefined): BadgeProps['variant'] {
  const normalized = String(status || '').trim().toUpperCase();
  return statusVariantMap[normalized] || 'default';
}

/**
 * Utility function to get display label for a status
 */
export function getStatusLabel(status: StatusType | string | null | undefined): string {
  const normalized = String(status || '').trim().toUpperCase();
  return statusLabelMap[normalized] || formatEnumLabel(normalized);
}

/**
 * Converts enum-like API values into user-facing labels without changing submitted values.
 */
export function formatEnumLabel(value: string | null | undefined): string {
  const normalized = String(value || '').trim();
  if (!normalized) {
    return '';
  }

  const upperValue = normalized.toUpperCase();
  const mapped = enumLabelMap[upperValue];
  if (mapped) {
    return mapped;
  }

  return normalized
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .filter(Boolean)
    .map((part, index) => formatEnumPart(part, index))
    .join(' ');
}

function formatEnumPart(part: string, index: number): string {
  const upper = part.toUpperCase();
  const lower = part.toLowerCase();
  if (enumAcronyms.has(upper)) {
    return upper;
  }
  if (index > 0 && enumLowercaseWords.has(lower)) {
    return lower;
  }
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}
