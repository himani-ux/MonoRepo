export interface SafetyClosureIncident {
  id: number;
  incident_number: string | null;
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_id: string;
  vessel_name?: string | null;
  record_type: string;
  state: string;
  current_phase: number;
  risk_band: "GREEN" | "YELLOW" | "RED" | null;
  imo_classifier: string | null;
  occurred_at: string | null;
  reported_at: string | null;
  narrative: string | null;
  dpa_accepted_at: string | null;
  dpa_accepted_by: string | null;
  fm_approved_at: string | null;
  fm_approved_by: string | null;
  closed_at: string | null;
  closure_reason: string | null;
  reporter_name?: string | null;
  reporter_rank?: string | null;
}

export interface SafetyClosurePhaseLog {
  id: number;
  phase_from: number | null;
  phase_to: number;
  transition_type: string;
  loop_back_reason: string | null;
  actor_user_id: string;
  actor_role_code: string;
  occurred_at: string;
}

export interface SafetyClosureFieldHistory {
  id: number;
  field_name: string;
  old_value: unknown;
  new_value: unknown;
  change_reason: string | null;
  actor_user_id: string;
  actor_role_code: string;
  changed_at: string;
}

export interface SafetyClosureSignatureStatus {
  required: boolean;
  present: boolean;
}

export interface SafetyClosureExport {
  available: boolean;
  endpoint: string;
}

export interface SafetyIncidentClosureSummary {
  incident: SafetyClosureIncident;
  audit_summary: {
    phase_log_count: number;
    field_history_count: number;
    latest_phase_log: SafetyClosurePhaseLog | null;
    latest_field_change: SafetyClosureFieldHistory | null;
  };
  phase_logs?: SafetyClosurePhaseLog[];
  field_history?: SafetyClosureFieldHistory[];
  signature_chain?: Record<string, SafetyClosureSignatureStatus>;
  exports?: {
    incident_pdf?: SafetyClosureExport;
    msc_mepc3?: SafetyClosureExport;
    auditor_zip?: SafetyClosureExport;
  };
}
