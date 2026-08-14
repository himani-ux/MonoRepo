export type AuditChecklistWalkStatus = 'NOT_REVIEWED' | 'COMPLIANT' | 'ADD_FINDING';

export interface AuditChecklistItem {
  id: string;
  location_code: string;
  item_code: string;
  question: string;
  guideline: string;
  regulation_ref: string;
  ksm_sms_ref: string;
  ship_type: string;
  sequence_no: number;
}

export interface AuditChecklistHeader {
  id: string;
  checklist_code: string;
  name: string;
  auditee_type: string;
  scope_dept: string | null;
  ship_type_scope: string | null;
  source_form_ref: string;
  code_version: string | null;
}

export interface AuditChecklist {
  audit_id: string;
  selected: boolean;
  ship_type_filter: string | null;
  item_filter_applied: boolean;
  checklist: AuditChecklistHeader | null;
  items: AuditChecklistItem[];
}
