export interface SafetySignatureStatus {
  present: boolean;
  required: boolean;
}

export interface SafetySignatureChainStatus {
  reporter: SafetySignatureStatus;
  master: SafetySignatureStatus;
  hod: SafetySignatureStatus;
  dpa: SafetySignatureStatus;
  fm: SafetySignatureStatus;
  pic: SafetySignatureStatus;
}

export interface SafetyPdfPreviewStatus {
  available: boolean;
  download_path?: string;
  expected_sections: number;
  incident_id: number;
  message: string;
  status: string;
}

export interface SafetyPhase7Authority {
  assigned_pic_user_id: string | null;
  allowed_role_codes: string[];
  required_process_id: string;
  message: string;
}

export interface SafetyIncidentPhase7Preflight {
  incident_id: number;
  current_phase: number;
  risk_band: "GREEN" | "YELLOW" | "RED" | null;
  bias_guards_resolved: boolean;
  root_count: number;
  recommendation_tier_count: Record<string, number>;
  alarp_complete: boolean;
  signature_chain_status: SafetySignatureChainStatus;
  closer_role: "PIC" | "DPA" | "FM";
  required_process_id: string;
  authority?: SafetyPhase7Authority;
  ready_for_acceptance: boolean;
  blockers: string[];
  pdf_preview: SafetyPdfPreviewStatus;
  generated_at: string;
}
