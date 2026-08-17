export const AUDIT_SCORECARD_STATUSES = [
  'SATISFACTORY',
  'NEEDS_IMPROVEMENT',
  'NC_RAISED',
  'N_A',
] as const;

export type AuditScorecardStatus = (typeof AUDIT_SCORECARD_STATUSES)[number];

export interface AuditDetailEditableFields {
  audit_scope: string;
  terms_of_reference: string;
  audit_summary: string;
  equipment_tested: string;
  opening_meeting_at?: string | null;
  closing_meeting_at?: string | null;
  prev_internal_ca_verified?: 'YES' | 'NO' | 'NA' | '';
  prev_external_ca_verified?: 'YES' | 'NO' | 'NA' | '';
}

export interface AuditScorecardRow {
  area_code: string;
  display_name: string;
  is_vessel_only: boolean;
  sequence_no: number;
  status: AuditScorecardStatus | null;
  remarks: string;
}

export interface AuditFindingRow {
  id: string;
  finding_type: 'NC' | 'OBSERVATION' | string;
  nc_category: string | null;
  observation_category: string | null;
  standard_code: string | null;
  clause_ref_text: string | null;
  description: string;
  objective_evidence: string | null;
  priority: string;
  is_fleetwide_relevance: boolean;
  linked_circular_id: string | null;
  psc_deficiency_id: string;
  car_id: string | null;
  car_number: string | null;
  car_status: string | null;
}

export interface AuditDetail {
  id: string;
  inspection_id: string;
  inspection: {
    id: string;
    vessel_id: string;
    inspection_date: string;
    port_place: string;
    country: string;
    authority: string;
    inspector_name: string;
    report_reference: string;
  };
  audit_classification: string;
  auditee_type: 'VESSEL' | 'OFFICE_DEPT' | string;
  auditee_office_dept: string | null;
  audit_subtype: string;
  lead_auditor_name: string;
  lead_auditor_designation: string | null;
  lead_auditor_company: string;
  lead_auditor_qual: string | null;
  trigger_reason: string;
  audit_start_date: string;
  audit_end_date: string | null;
  opening_meeting_at: string | null;
  closing_meeting_at: string | null;
  audit_scope: string;
  terms_of_reference: string;
  audit_summary: string;
  equipment_tested: string;
  prev_internal_ca_verified: 'YES' | 'NO' | 'NA' | '';
  prev_external_ca_verified: 'YES' | 'NO' | 'NA' | '';
  status: string;
  external_audit_subtypes?: string[];
  external_audit_org_id?: string | null;
  external_audit_org_type?: string;
  external_lead_auditor_name?: string;
  external_lead_auditor_credential?: string;
  flag_state_code?: string;
  cycle_year?: number | null;
  linked_cert_ids?: string[];
  certificate_impact?: string;
  external_closure_status?: string;
  is_cycle_resetting?: boolean;
  cycle_reset_reason?: string;
  standards: string[];
  team_members: Array<{
    id: string;
    member_name: string;
    member_designation: string;
    member_company: string;
    member_role: string;
    sequence_no: number;
  }>;
  attendees: Array<{
    id: string;
    attendee_name: string;
    attendee_rank: string;
    opening_present: boolean;
    closing_present: boolean;
    sequence_no: number;
  }>;
  counts: {
    nc: number;
    observations: number;
    total_findings: number;
  };
  effective_permissions?: string[];
  scorecard: AuditScorecardRow[];
  findings: AuditFindingRow[];
}

export function detailEditableFields(audit: AuditDetail): AuditDetailEditableFields {
  return {
    audit_scope: audit.audit_scope || '',
    terms_of_reference: audit.terms_of_reference || '',
    audit_summary: audit.audit_summary || '',
    equipment_tested: audit.equipment_tested || '',
    opening_meeting_at: audit.opening_meeting_at || null,
    closing_meeting_at: audit.closing_meeting_at || null,
    prev_internal_ca_verified: audit.prev_internal_ca_verified || '',
    prev_external_ca_verified: audit.prev_external_ca_verified || '',
  };
}
