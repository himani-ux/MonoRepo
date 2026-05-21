export interface SafetyRecommendationVerification {
  recommendation_id: number;
  is_effective: boolean;
  residual_risk: string;
  verified_at: string;
  verified_by: string;
  notes: string | null;
}

export interface SafetyPhase8RecommendationRow {
  id: number;
  tier: string;
  title: string;
  action_completed: boolean;
  verification_deferred: boolean;
  corrective_action_count: number;
  latest_verification: SafetyRecommendationVerification | null;
}

export interface SafetyPhase8DeadlinePause {
  is_paused: boolean;
  state: string;
  last_event_at: string | null;
  last_actor_user_id: string | null;
}

export interface SafetyPhase8PicRetention {
  retained: boolean;
  retained_pic_user_id: string | null;
  replacement_access: string;
}

export interface SafetyPhase8WorkspacePayload {
  incident_id: number;
  current_phase: number;
  state: string;
  risk_band: "GREEN" | "YELLOW" | "RED" | null;
  required_process_id: string;
  recommendations: SafetyPhase8RecommendationRow[];
  corrective_actions_summary: {
    total: number;
    open: number;
    in_progress: number;
    pending_verify: number;
    closed: number;
  };
  physical_verification: {
    done: number;
    pending: number;
    separate_track: boolean;
  };
  deadline_pause: SafetyPhase8DeadlinePause;
  pic_retention: SafetyPhase8PicRetention;
  ready_for_close: boolean;
  blockers: string[];
}
