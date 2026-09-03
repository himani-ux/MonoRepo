export const RCA_METHODS = ['FIVE_WHY', 'FISHBONE_ISHIKAWA', 'STRUCTURED_NARRATIVE', 'OTHER'] as const;
export const ROOT_CAUSE_CATEGORIES = [
  'PROCEDURAL_GAP',
  'TRAINING_GAP',
  'SUPERVISION_FAILURE',
  'COMMUNICATION_FAILURE',
  'EQUIPMENT_FAILURE',
  'HUMAN_ERROR',
  'MANAGEMENT_SYSTEM_FAILURE',
  'OTHER',
] as const;
export const CERTIFICATES_AT_RISK = ['DOC', 'SMC', 'ISSC', 'MLC_DMLC', 'NONE'] as const;
export const EFFECTIVENESS_REVIEW_METHODS = [
  'VESSEL_FOLLOWUP_INSPECTION',
  'REVIEW_SUBSEQUENT_AUDIT',
  'OFFICE_DOC_REVIEW',
  'MASTERS_REPORT',
] as const;
export const EFFECTIVENESS_OUTCOMES = ['EFFECTIVE', 'PARTIALLY_EFFECTIVE', 'NOT_EFFECTIVE'] as const;
export const ACCEPTANCE_DECISIONS = ['ACCEPTED', 'RETURNED'] as const;
export const VERIFICATION_METHODS = [
  'DOCUMENT_REVIEW',
  'ONBOARD_VERIFICATION',
  'PSC_AUTHORITY_CLEARANCE',
  'NEXT_PERIODIC_SURVEY',
] as const;
export const CERTIFICATE_ENDORSEMENT_TYPES = ['DOC', 'SMC', 'ISSC', 'MLC_DMLC', 'NONE'] as const;
export const FINAL_CLOSURE_STATUSES = ['CLOSED', 'CONDITIONALLY_CLOSED', 'NOT_CLOSED'] as const;

export type AuditNcPartName = 'part-b' | 'part-c' | 'part-d' | 'part-e' | 'part-f' | 'part-g';
export type AuditNcWorkflowAction =
  | 'DRAFT_FOR_VESSEL'
  | 'SUBMIT_TO_PIC'
  | 'START_PIC_REVIEW'
  | 'SUBMIT_TO_LEAD_AUDITOR'
  | 'LEAD_AUDITOR_CLOSE'
  | 'REQUEST_REWORK';

export interface AuditNcClosure {
  id: string;
  finding_id: string;
  audit_detail_id: string;
  car: {
    id: string;
    car_number: string;
    status: string;
    target_date: string | null;
  };
  part_a: {
    nc_reference_no: string;
    audit_date: string | null;
    vessel_id: string;
    port_place: string;
    auditor_name: string;
    auditor_organisation: string;
    rule_book_type: string | null;
    clause_ref_text: string | null;
    objective_evidence: string;
    nc_issued_date: string | null;
    required_closure_deadline: string | null;
    certificates_at_risk: string;
    nc_classification: string | null;
    description: string;
  };
  part_b: AuditNcPartB;
  part_c: AuditNcPartC;
  part_d: AuditNcPartD;
  part_e: AuditNcPartE;
  part_f: AuditNcPartF;
  part_g: AuditNcPartG;
}

export interface AuditRcaTemplate {
  id: string;
  category: string;
  title: string;
  template_text: string;
  example_evidence_hint: string;
  applicable_def_categories: string;
  code_version: string;
}

export interface AuditRcaTemplateMaster {
  category: string;
  templates: AuditRcaTemplate[];
}

export interface AuditNcPartB {
  immediate_action_text: string;
  immediate_action_completed_at: string | null;
  master_immediate_sign_name: string;
  master_immediate_sign_at: string | null;
  drafted_by_user_id: string;
}

export interface AuditNcPartC {
  rca_method: string;
  rca_method_other: string;
  rca_template_id: string | null;
  problem_statement: string;
  why_1: string;
  why_2: string;
  why_3: string;
  why_4: string;
  why_5: string;
  root_cause_categories: string[];
  root_cause_summary: string;
  clc_item_ids: string[];
  custom_cause_text: string;
}

export interface AuditNcPartD {
  corrective_action_text: string;
  target_completion_date: string | null;
  actual_completion_date: string | null;
  preventive_action_text: string;
  sms_amendment_required: boolean;
  sms_amendment_doc_ref: string;
}

export interface AuditNcPartE {
  certificates_at_risk?: string[];
  effectiveness_review_date: string | null;
  effectiveness_review_method: string;
  effectiveness_assessment_text: string;
  effectiveness_outcome: string;
  effectiveness_further_action_text: string;
  effectiveness_signer_name: string;
  effectiveness_signer_at: string | null;
  effectiveness_overdue: boolean;
}

export interface AuditNcPartF {
  certificates_at_risk?: string[];
  acceptance_review_date: string | null;
  acceptance_rca_adequacy_text: string;
  acceptance_decision: string;
  acceptance_return_reason: string;
  acceptance_signer_name: string;
  acceptance_signer_at: string | null;
}

export interface AuditNcPartG {
  verifying_auditor_name: string;
  verifying_authority_org: string;
  verification_method: string;
  certificate_endorsement_type: string;
  certificate_endorsement_ref: string;
  auditor_assessment_text: string;
  final_closure_status: string;
  resubmit_by_date: string | null;
  auditor_verification_sign_at: string | null;
}

export type AuditNcPartPayload =
  | Partial<AuditNcPartB>
  | Partial<AuditNcPartC>
  | Partial<AuditNcPartD>
  | Partial<AuditNcPartE>
  | Partial<AuditNcPartF>
  | Partial<AuditNcPartG>;

export type AuditNcDraftPayload = Partial<AuditNcPartB & AuditNcPartC> & {
  comment?: string;
};

export interface AuditNcWorkflowResponse {
  id: string;
  status: string;
  action: AuditNcWorkflowAction;
}
