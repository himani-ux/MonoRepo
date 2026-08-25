export const AUDIT_PLAN_STATUSES = [
  'PLANNED',
  'CONFIRMED',
  'IN_PROGRESS',
  'COMPLETED',
  'EXTENSION_REQUESTED',
  'EXTENDED',
  'OVERDUE',
  'CRITICAL_OVERDUE',
  'CANCELLED',
] as const;

export const AUDIT_PLAN_WRITABLE_STATUSES = ['PLANNED', 'CONFIRMED'] as const;

export type AuditPlanStatus = (typeof AUDIT_PLAN_STATUSES)[number];
export type AuditPlanWritableStatus = (typeof AUDIT_PLAN_WRITABLE_STATUSES)[number];

export interface AuditPlan {
  id: string;
  target_vessel_id: string | null;
  target_office_dept: string | null;
  target_label: string;
  audit_classification: 'INTERNAL' | string;
  audit_standards_csv: string;
  lead_auditor_user_id: string | null;
  lead_auditor_name: string;
  lead_auditor_designation: string;
  lead_auditor_company: string;
  lead_auditor_qual: string;
  planned_window_start: string | null;
  planned_window_end: string | null;
  window_label: string;
  extended_due_date: string | null;
  extension_form_ref: string | null;
  extension_requested_at: string | null;
  extension_requested_by: string | null;
  extension_requested_reason: string | null;
  extension_approved_at: string | null;
  extension_approved_by: string | null;
  extension_approved_reason: string | null;
  flag_notified: boolean;
  flag_notification_date: string | null;
  flag_notification_ref: string | null;
  flag_notification_attachment: string | null;
  is_additional: boolean;
  additional_reason: string | null;
  trigger_event_type: string | null;
  trigger_event_ref: string | null;
  cancellation_reason: string | null;
  next_planned_date: string | null;
  cancelled_by: string | null;
  cancelled_at: string | null;
  status: AuditPlanStatus | string;
  created_by: string | null;
  created_date: string | null;
  updated_by: string | null;
  updated_date: string | null;
}

export interface AuditPlanList {
  count: number;
  results: AuditPlan[];
}

export interface AuditPlanFormData {
  target_vessel_id: string;
  target_office_dept: string;
  audit_classification: 'INTERNAL';
  audit_standards_csv: string;
  lead_auditor_user_id: string;
  planned_window_start: string;
  planned_window_end: string;
  status: AuditPlanWritableStatus;
}

export interface AuditPlanExtensionRequestData {
  extension_requested_reason: string;
  proposed_new_target_date: string;
}

export interface AuditPlanExtensionDecisionData {
  decision: 'APPROVE' | 'REJECT';
  extension_approved_reason: string;
}

export interface AuditPlanFlagNotificationData {
  flag_notification_date: string;
  flag_notification_ref: string;
  flag_notification_attachment: string;
}

export interface AuditPlanCancelData {
  cancellation_reason: string;
  next_planned_date: string;
}

export interface AuditPlanAdditionalData extends AuditPlanFormData {
  additional_reason: string;
  trigger_event_type: string;
  trigger_event_ref: string;
}

export const emptyAuditPlanForm: AuditPlanFormData = {
  target_vessel_id: '',
  target_office_dept: '',
  audit_classification: 'INTERNAL',
  audit_standards_csv: 'ISM',
  lead_auditor_user_id: '',
  planned_window_start: '',
  planned_window_end: '',
  status: 'PLANNED',
};

export const emptyAuditPlanExtensionRequest: AuditPlanExtensionRequestData = {
  extension_requested_reason: '',
  proposed_new_target_date: '',
};

export const emptyAuditPlanExtensionDecision: AuditPlanExtensionDecisionData = {
  decision: 'APPROVE',
  extension_approved_reason: '',
};

export const emptyAuditPlanFlagNotification: AuditPlanFlagNotificationData = {
  flag_notification_date: '',
  flag_notification_ref: '',
  flag_notification_attachment: '',
};

export const emptyAuditPlanCancel: AuditPlanCancelData = {
  cancellation_reason: '',
  next_planned_date: '',
};

export const emptyAuditPlanAdditional: AuditPlanAdditionalData = {
  ...emptyAuditPlanForm,
  additional_reason: '',
  trigger_event_type: 'PSC_INSPECTION',
  trigger_event_ref: '',
};

export function auditPlanFormFromPlan(plan: AuditPlan): AuditPlanFormData {
  return {
    target_vessel_id: plan.target_vessel_id || '',
    target_office_dept: plan.target_office_dept || '',
    audit_classification: 'INTERNAL',
    audit_standards_csv: plan.audit_standards_csv || 'ISM',
    lead_auditor_user_id: plan.lead_auditor_user_id || '',
    planned_window_start: plan.planned_window_start || '',
    planned_window_end: plan.planned_window_end || '',
    status: plan.status === 'CONFIRMED' ? 'CONFIRMED' : 'PLANNED',
  };
}
