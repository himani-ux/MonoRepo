export type SafetyLossEvaluationReportType = 'INCIDENT' | 'INJURY';

export interface SafetyLossEvaluationOption<T = string | boolean> {
  value: T;
  label: string;
  id?: string;
}

export interface SafetyIncidentLossEvaluation {
  id: string | null;
  consequence: string | null;
  likelihood: string | null;
  risk_level: string | null;
  name_of_master: string | null;
  name_of_chief_engineer: string | null;
  repair_type: string | null;
  repair_details: string | null;
  last_overhaul_maintenance_survey_details: string | null;
  safe_working_practice: string | null;
  man_hours_worked: string | null;
  hours_worked_previous_day: string | null;
  hours_rest_last_96_hours: string | null;
  delay_to_vessel: string | null;
  delay_reason: string | null;
  repair_man_hours_lost: string | null;
  materials_used_repairs_onboard: string | null;
  materials_specify_details: string | null;
  materials_reason: string | null;
  deviation: boolean | null;
  off_hire: boolean | null;
  injury_man_hours_lost: string | null;
  injury_reasons: string | null;
  repatriation: boolean | null;
  hospitalization: boolean | null;
  evacuation: boolean | null;
  estimated_cost_off_hire: string | null;
  estimated_cost_delay: string | null;
  estimated_cost_man_hours: string | null;
  estimated_cost_deviation: string | null;
  estimated_cost_materials: string | null;
  estimated_cost_miscellaneous: string | null;
  total_estimated_cost: string | null;
  miscellaneous_expenses_reason: string | null;
  cost_medicines_onboard: string | null;
  cost_doctor_visits: string | null;
  cost_repatriation: string | null;
  cost_evacuation: string | null;
  cost_injury_delay: string | null;
  cost_injury_man_hours: string | null;
  cost_injury_deviation: string | null;
  cost_injury_miscellaneous: string | null;
  injury_total_estimated_cost: string | null;
  injury_miscellaneous_expenses_reason: string | null;
  updated_date: string | null;
}

export interface SafetyPhase8DeadlinePause {
  is_paused: boolean;
  state: string;
  last_event_at: string | null;
  last_actor_user_id: string | null;
}

export interface SafetyPhase8WorkspacePayload {
  incident_id: string;
  current_phase: number;
  state: string;
  risk_band: 'GREEN' | 'YELLOW' | 'RED' | null;
  required_process_id: string;
  phase_title: 'Loss Evaluation';
  report_type: SafetyLossEvaluationReportType;
  has_loss_evaluation: boolean;
  loss_evaluation: SafetyIncidentLossEvaluation;
  choices: {
    consequence: Array<SafetyLossEvaluationOption<string>>;
    likelihood: Array<SafetyLossEvaluationOption<string>>;
    risk_level: Array<SafetyLossEvaluationOption<string>>;
    repair_type: Array<SafetyLossEvaluationOption<string>>;
    yes_no: Array<SafetyLossEvaluationOption<boolean>>;
    safe_working_practice: Array<SafetyLossEvaluationOption<string>>;
  };
  ready_for_close: boolean;
  blockers: string[];
  blocker_details: Array<{
    code: string;
    message: string;
  }>;
  deadline_pause?: SafetyPhase8DeadlinePause;
  corrective_actions_summary?: {
    total: number;
    open: number;
    in_progress: number;
    pending_verify: number;
    closed: number;
  };
  physical_verification?: {
    done: number;
    pending: number;
    separate_track: boolean;
  };
  pic_retention?: {
    retained: boolean;
    retained_pic_user_id: string | null;
    replacement_access: string;
  };
  recommendations?: Array<{
    id: string;
    tier: string;
    title: string;
    action_completed: boolean;
    latest_verification: {
      is_effective: boolean;
    } | null;
  }>;
}
