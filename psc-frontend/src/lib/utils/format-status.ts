import type { BadgeProps } from '@/components/ui';
import type { InspectionStatus, OperationalStatus, CARStatus, DefStatus } from '@/types';

export type StatusType = InspectionStatus | OperationalStatus | CARStatus | DefStatus | 'OVERDUE' | 'DETENTION';

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
export function getStatusVariant(status: StatusType): BadgeProps['variant'] {
  return statusVariantMap[status] || 'default';
}

/**
 * Utility function to get display label for a status
 */
export function getStatusLabel(status: StatusType): string {
  return statusLabelMap[status] || status;
}
