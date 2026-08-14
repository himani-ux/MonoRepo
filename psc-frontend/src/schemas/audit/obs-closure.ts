export const OBS_ACCEPTANCE_DECISIONS = ['ACCEPTED', 'RETURNED'] as const;
export const OBS_VERIFICATION_METHODS = [
  'DOCUMENT_REVIEW',
  'ONBOARD_VERIFICATION',
  'NEXT_AUDIT',
  'REMOTE_REVIEW',
] as const;
export const OBS_CLOSURE_STATUSES = ['CLOSED', 'PARTIALLY_CLOSED', 'NOT_CLOSED'] as const;

export type AuditObsState = 'NOT_STARTED' | 'IN_PROGRESS' | 'SUBMITTED' | 'MASTER_CLOSED';
export type AuditObsPartName = 'part-b' | 'part-c' | 'part-d';

export interface AuditObsClosure {
  id: string;
  finding_id: string;
  audit_detail_id: string;
  state: AuditObsState;
  car: {
    id: string;
    car_number: string;
    status: string;
    target_date: string | null;
  };
  part_a: {
    observation_reference_no: string;
    audit_date: string | null;
    vessel_id: string;
    port_place: string;
    auditor_name: string;
    auditor_organisation: string;
    rule_book_type: string | null;
    clause_ref_text: string | null;
    objective_evidence: string;
    observation_issued_date: string | null;
    required_closure_deadline: string | null;
    observation_category: string | null;
    description: string;
  };
  part_b: AuditObsPartB;
  part_c: AuditObsPartC;
  part_d: AuditObsPartD;
}

export interface AuditObsPartB {
  responded_by_name: string;
  responded_by_rank: string;
  target_closure_date: string | null;
  immediate_action_text: string;
  root_cause_text: string;
  corrective_action_text: string;
  preventive_action_text: string;
  sms_amendment_required: boolean;
  sms_amendment_doc_ref: string;
  actual_closure_date: string | null;
  master_sign_name: string;
  master_sign_at: string | null;
}

export interface AuditObsPartC {
  acceptance_review_date: string | null;
  acceptance_adequacy_text: string;
  acceptance_decision: string;
  acceptance_return_reason: string;
  acceptance_signer_name: string;
  acceptance_signer_at: string | null;
}

export interface AuditObsPartD {
  verifying_auditor_name: string;
  verifying_authority_org: string;
  verification_method: string;
  auditor_remarks_text: string;
  closure_status: string;
  resubmit_by_date: string | null;
  auditor_verification_sign_at: string | null;
}

export type AuditObsPartPayload =
  | Partial<AuditObsPartB>
  | Partial<AuditObsPartC>
  | Partial<AuditObsPartD>;
