import { apiClient } from './client';
import { API_BASE_URL } from '@/lib/utils/constants';

const SAFETY_API_BASE_URL = `${API_BASE_URL}/api/safety`;

function buildSafetyApiUrl(path: string): string {
  return `${SAFETY_API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

function buildParams(
  params: Record<string, string | number | boolean | null | undefined>
) {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') {
      continue;
    }
    searchParams.set(key, String(value));
  }
  return searchParams;
}

export type SafetyDashboardPeriodCode = '90D' | '12M' | '3Y';
export type SafetyScoreStatus = 'GREEN' | 'AMBER' | 'RED';

export interface SafetyDashboardVesselOption {
  id: string;
  vessel_code: string;
  vessel_name: string;
}

export interface SafetyReferenceMscatOption {
  id: string;
  legacy_int_id: number;
  category_id: number;
  category_name: string;
  subcode_id: string;
  subcode_description: string;
  cause_type: string;
  active: boolean;
}

export type SafetyReferenceImmediateCauseOption = SafetyReferenceMscatOption;

export interface SafetyNearMissCauseOption {
  id: string;
  factor: 'HUMAN' | 'VESSEL' | 'MANAGEMENT' | 'OTHER';
  factor_label: string;
  cause_stage: 'IMMEDIATE' | 'ROOT';
  cause_stage_label: string;
  option_code: string;
  option_text: string;
  display_order: number;
  active: boolean;
}

export interface SafetyNearMissCategoryOption {
  id: string;
  category_name: string;
  display_order: number;
  active: boolean;
}

export interface SafetyReferenceLossTypeOption {
  id: string;
  legacy_int_id: number;
  loss_type_id: number;
  loss_type_name: string;
  description: string | null;
  active: boolean;
}

export interface SafetyReferenceIncidentTypeOption {
  id: string;
  legacy_int_id: number;
  type_code: string;
  type_name: string;
  imo_reportable: boolean;
  description: string | null;
  active: boolean;
}

export type SafetyIncidentWeatherFieldKey =
  | 'VISIBILITY'
  | 'PRECIPITATION'
  | 'SEA_STATE'
  | 'WIND_SCALE'
  | 'WIND_DIRECTION'
  | 'LIGHTING_SOURCE'
  | 'CURRENT_DIRECTION'
  | 'ICE_CONDITION_ONBOARD'
  | 'ICE_CONDITION_AT_SEA'
  | 'LIGHT_CONDITION';

export interface SafetyIncidentWeatherOption {
  id: string;
  field_key: SafetyIncidentWeatherFieldKey;
  field_label: string;
  option_label: string;
  display_order: number;
  active: boolean;
}

export type SafetyInjuryDropdownFieldKey =
  | 'NATURE_OF_INJURY'
  | 'SOURCE_OF_INJURY'
  | 'AFFECTED_BODY_AREA'
  | 'TYPE_OF_ACTIVITY'
  | 'SAFE_WORKING_PRACTICE';

export interface SafetyInjuryDropdownOption {
  id: string;
  field_key: SafetyInjuryDropdownFieldKey;
  field_label: string;
  option_label: string;
  display_order: number;
  active: boolean;
}

export interface SafetyReferenceSoiAreaOption {
  id: string;
  legacy_int_id: number;
  area_id: number;
  area_name: string;
  section_12_flag: boolean;
  display_order: number;
  active: boolean;
}

export interface SafetyReferenceSoiItemOption {
  id: string;
  legacy_int_id: number;
  area_id: number;
  area_name: string;
  subsection_id: string;
  subsection_name: string;
  item_number: string;
  description: string;
  tier: string;
  active: boolean;
}

export interface SafetyReferenceChecklistVersionOption {
  id: string;
  legacy_int_id: number;
  version_label: string;
  effective_from: string;
  effective_to: string | null;
  source_description: string;
  active: boolean;
}

export interface SafetyReferenceBiasGuardOption {
  id: string;
  legacy_int_id: number;
  guard_code: string;
  guard_name: string;
  family: string;
  description: string;
  bit_position: number;
  active: boolean;
}

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

function unwrapPaginatedResults<T>(payload: T[] | PaginatedResponse<T>): T[] {
  if (Array.isArray(payload)) {
    return payload;
  }
  return Array.isArray(payload.results) ? payload.results : [];
}

export interface SafetyDashboardCompositeResponse {
  available_vessels: SafetyDashboardVesselOption[];
  calculated_at: string;
  component_scores: Record<string, number>;
  composite_score: number;
  metrics: {
    open_findings: number;
    open_incidents: number;
    open_near_misses: number;
    overdue_corrective_actions: number;
    soi_compliance_display: string | null;
    soi_compliance_label: string;
    soi_compliance_percent: number | null;
  };
  period_code: SafetyDashboardPeriodCode;
  scope_id: string;
  scope_type: 'FLEET' | 'VESSEL';
  score_status: SafetyScoreStatus;
  window_end: string;
  window_start: string;
}

export interface SafetyDashboardHeinrichResponse {
  confidence: {
    incident_count_12m: number;
    near_miss_count_12m: number;
    reason: string;
    status: SafetyScoreStatus;
    tooltip: string;
  };
  layers: Array<{
    actual: number;
    benchmark: number;
    key: string;
    label: string;
    variance: number;
  }>;
  reporting_culture_gap: {
    is_gap: boolean;
    message: string;
  };
  scope_id: string;
  scope_type: 'FLEET' | 'VESSEL';
  window_end: string;
  window_start: string;
}

export interface SafetyDashboardRepeatRootRadarResponse {
  fleet: Array<{
    category_name: string;
    description: string;
    occurrences: number;
    relative_strength: number;
    subcode_id: string;
    vessel_count: number;
  }>;
  minimum_repeat_count: number;
  scope_id: string;
  scope_type: 'FLEET' | 'VESSEL';
  vessel: Array<{
    category_name: string;
    description: string;
    occurrences: number;
    relative_strength: number;
    subcode_id: string;
    vessel_count: number;
  }>;
  window_end: string;
  window_start: string;
}

export interface SafetyDashboardParetoResponse {
  entries: Array<{
    category_name: string;
    cumulative_percent: number;
    description: string;
    occurrences: number;
    rank: number;
    share_percent: number;
    subcode_id: string;
    vessel_code?: string | null;
    vessel_display_name?: string | null;
    vessel_id: string;
    vessel_name?: string | null;
    within_80_cutoff: boolean;
  }>;
  scope_id: string;
  scope_type: 'FLEET' | 'VESSEL';
  top_n: number;
  total_occurrences: number;
  window_end: string;
  window_start: string;
}

export interface SafetyDashboardSoiComplianceResponse {
  current_vessel: {
    applicable_area_count: number;
    compliance_percent: number | null;
    display_value: string;
    inspected_area_count: number;
    overdue_area_count: number;
    status: string;
    vessel_id: string;
  };
  fleet_average: {
    compliance_percent: number | null;
    display_value: string;
    note: string;
    vessel_count: number;
  };
  label: string;
}

export interface SafetyDashboardCaAgingResponse {
  buckets: Array<{
    bucket: string;
    count: number;
    label: string;
  }>;
  label: string;
  note: string;
  oldest_age_days: number;
  open_action_count: number;
  scope_id: string;
  scope_type: 'FLEET' | 'VESSEL';
}

export interface SafetyIncidentListItem {
  created_date: string;
  current_phase: number;
  draft_reference: string | null;
  id: string;
  imo_classifier: string | null;
  incident_number: string | null;
  occurred_at: string | null;
  record_type: 'INCIDENT';
  reported_at: string | null;
  risk_band: string | null;
  schema_version: number;
  state: string;
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_id: string;
  vessel_name?: string | null;
}

export interface SafetyNearMissListItem {
  id: string;
  incident_number: string | null;
  incident_type_id?: number | null;
  loss_type_primary_id?: number | null;
  near_miss_priority: string | null;
  near_miss_severity?: 'HIGH' | 'MED' | 'LOW' | null;
  near_miss_place?: 'AT_ANCHOR' | 'AT_SEA' | 'AT_PORT' | null;
  near_miss_shell_tag?: string | null;
  near_miss_category_tags?: string[];
  near_miss_incident_type_ids?: number[];
  near_miss_mscat_category_id?: number | null;
  near_miss_mscat_subcode_id?: string | null;
  near_miss_mscat_subcode_ids?: string[];
  near_miss_factor_causes?: Array<{
    factor: 'HUMAN' | 'VESSEL' | 'MANAGEMENT' | 'OTHER';
    immediate_option_id: string;
    immediate_option_text?: string;
    immediate_other_text?: string;
    root_option_id: string;
    root_option_text?: string;
    root_other_text?: string;
  }>;
  near_miss_immediate_action?: string | null;
  near_miss_suggestion?: string | null;
  near_miss_root_cause_detail?: string | null;
  near_miss_corrective_action?: string | null;
  near_miss_weather_voyage_details?: string | null;
  near_miss_equipment_details?: string | null;
  near_miss_lessons_learned?: string | null;
  occurred_at: string | null;
  record_type: 'NEAR_MISS';
  reported_at: string | null;
  reporter_name: string | null;
  schema_version: number;
  state: string;
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_id: string;
  vessel_name?: string | null;
}

export interface SafetyScmSection {
  agenda_item_number: number;
  auto_populated: boolean;
  content: string;
  decision: string | null;
  legacy_field_meta?: SafetyScmLegacyFieldMeta[];
  legacy_fields?: Record<string, string | number | boolean | null>;
  schema_version: number;
  section_label: string;
}

export interface SafetyScmLegacyFieldMeta {
  field_key: string;
  field_label: string;
  field_type: 'BOOLEAN' | 'DATE' | 'INTEGER' | 'TEXT';
  office_only?: boolean;
  required?: boolean;
}

export interface SafetyScmCadenceWarning {
  days_since_previous?: number | null;
  due_date?: string | null;
  is_overdue?: boolean;
  message?: string | null;
  status?: string | null;
}

export interface SafetyScmMeeting {
  ad_hoc_trigger_reason: string | null;
  cadence_warning: SafetyScmCadenceWarning | null;
  chair_crew_id: string | null;
  created_by: string | null;
  created_date: string;
  id: string;
  latitude: string | number | null;
  location: string | null;
  longitude: string | number | null;
  occasion: string;
  ship_position: 'S' | 'P' | string;
  ship_pos_from: string | null;
  ship_pos_to: string | null;
  comm_time: string | null;
  comp_time: string | null;
  master_signed_off_at: string | null;
  master_signed_off_by: string | null;
  meeting_date: string;
  meeting_time_local: string | null;
  meeting_type: string;
  office_comment: string | null;
  office_comment_at?: string | null;
  office_comment_by?: string | null;
  is_reviewed?: boolean;
  prepared_by_crew_id: string | null;
  attendance_warnings_acknowledged_at: string | null;
  attendance_warnings_acknowledged_by: string | null;
  schema_version: number;
  scm_number: string | null;
  sections: SafetyScmSection[];
  state: string;
  updated_by: string | null;
  updated_date: string;
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_id: string;
  vessel_name?: string | null;
  voyage_no: string | null;
}

export interface SafetyScmAgendaActionItem {
  assigned_crew_id: string | null;
  assigned_office_user_id: string | null;
  description: string;
  display_status: string;
  due_date: string | null;
  id: string;
  source_route: string;
  status: string;
  title: string;
}

export interface SafetyScmAgendaRow {
  action_item: SafetyScmAgendaActionItem | null;
  agenda_item_number: number;
  auto_populated: boolean;
  content: string;
  decision: string | null;
  id: string;
  legacy_field_meta?: SafetyScmLegacyFieldMeta[];
  legacy_fields?: Record<string, string | number | boolean | null>;
  linked_finding_ids: string[];
  linked_incident_ids: string[];
  schema_version?: number;
  section_label: string;
}

export interface SafetyScmCarriedForwardItem extends SafetyScmAgendaActionItem {
  agenda_item_number: number;
  section_label: string;
  source_meeting_id: string;
  source_scm_number: string;
}

export interface SafetyScmAgendaPayload {
  carried_forward_items: SafetyScmCarriedForwardItem[];
  meeting_date: string;
  meeting_id: string;
  meeting_state: string;
  meeting_type: string;
  rows: SafetyScmAgendaRow[];
  summary: {
    carried_forward_count: number;
    current_action_item_count: number;
    open_action_item_count: number;
  };
}

export interface SafetyScmAgendaUpdatePayload {
  rows: Array<{
    agenda_item_number: number;
    action_item?: {
      assigned_crew_id?: string | null;
      assigned_office_user_id?: string | null;
      description?: string;
      due_date?: string | null;
      enabled: boolean;
      title?: string;
    };
    content?: string;
    decision?: string | null;
    linked_finding_ids?: string[];
    linked_incident_ids?: string[];
  }>;
}

export interface SafetyScmClosedSinceLastCutoff {
  closed_at: string;
  meeting_id: string;
  meeting_type: string;
  scm_number: string;
}

export interface SafetyScmClosedSinceLastItem {
  closed_at: string;
  item_type: 'INCIDENT' | 'NEAR_MISS' | 'SOI_FINDING' | 'CORRECTIVE_ACTION';
  reference: string;
  source_id: string;
  source_route: string | null;
  status: string;
  title: string;
  unique_id: string | null;
}

export interface SafetyScmClosedSinceLastPayload {
  cutoff: SafetyScmClosedSinceLastCutoff | null;
  empty_message: string | null;
  items: SafetyScmClosedSinceLastItem[];
  meeting_id: number | null;
  summary: {
    corrective_action_count: number;
    incident_count: number;
    near_miss_count: number;
    soi_finding_count: number;
    total_count: number;
  };
  upper_bound_at: string | null;
  vessel_id: string;
}

export interface SafetyScmAutoFeedFinding {
  area_id: number;
  carried_forward_count: number;
  checklist_unique_id: string | null;
  created_date: string | null;
  description: string;
  due_date: string | null;
  finding_id: string;
  inspection_id: string;
  inspection_reference: string;
  priority: string;
  proposed_action: string | null;
  severity: string;
  source_route: string;
  status: string;
  title: string;
}

export interface SafetyScmAutoFeedPayload {
  carried_forward_findings: SafetyScmAutoFeedFinding[];
  cutoff: SafetyScmClosedSinceLastCutoff | null;
  empty_message: string | null;
  meeting_id: number | null;
  new_findings: SafetyScmAutoFeedFinding[];
  section8: {
    answer: 'YES' | 'NO';
    applicable_area_count: number;
    coverage_percent: number;
    inspected_area_count: number;
    inspection_count: number;
    summary_text: string;
  };
  summary: {
    carried_forward_count: number;
    new_count: number;
    total_count: number;
  };
  updated_finding_ids?: number[];
  vessel_id: string;
}

export interface SafetyScmCircularFeedItem {
  attachment_name: string;
  attachment_path: string;
  category: string;
  created_at: string | null;
  hashtags: string;
  id: string;
  msc_type?: string;
  office_instructions: string;
  publish_status: number | null;
  published_on: string | null;
  sr_no: string;
  title: string;
  vessel_id: string;
}

export interface SafetyScmNearMissFeedItem {
  closed_at: string | null;
  id: string;
  incident_number: string;
  occurred_at: string | null;
  priority: string;
  reported_at: string | null;
  severity: string;
  source_route: string;
  state: string;
  title: string;
}

export interface SafetyScmPscCarFeedItem {
  action_code: string;
  car_number: string;
  def_code: string;
  deficiency_description: string;
  id: string;
  inspection_date: string | null;
  port_place: string;
  source_route: string;
  status: string;
  target_date: string | null;
}

export interface SafetyScmAttendanceRow {
  absence_reason: string | null;
  crew_id: string;
  display_name: string;
  present: boolean;
  rank_name: string;
  remarks: string | null;
  schema_version: number;
  wrh_data_available: boolean;
  wrh_flag: 'GREEN' | 'YELLOW' | 'RED';
  wrh_non_compliance_flag: boolean;
  wrh_rest_hours_24h: number | string | null;
  wrh_rest_hours_7d: number | string | null;
  signature?: SafetyScmSignatureStatus;
}

export interface SafetyScmAttendancePayload {
  co_signature?: SafetyScmSignatureStatus;
  meeting_date: string;
  meeting_id: string;
  meeting_state: string;
  rows: SafetyScmAttendanceRow[];
  signature_summary?: {
    attendee_signature_count: number;
    co_signature_required: boolean;
    present_attendee_count: number;
    signatures_complete: boolean;
  };
  timezone_offset_minutes: number | null;
  warnings: string[];
}

export interface SafetyScmCreateAttendeeRow
  extends Pick<
    SafetyScmAttendanceRow,
    | 'absence_reason'
    | 'crew_id'
    | 'display_name'
    | 'present'
    | 'rank_name'
    | 'remarks'
    | 'schema_version'
  > {
  department: string;
  warning_codes: string[];
  warnings: string[];
  wrh_data_available: boolean;
  wrh_flag: 'GREEN' | 'YELLOW' | 'RED' | 'PENDING';
  wrh_non_compliance_flag: boolean;
  wrh_rest_hours_24h: number | string | null;
  wrh_rest_hours_7d: number | string | null;
}

export interface SafetyScmCrewSnapshot {
  crew_id: string;
  crew_name: string;
  department: string;
  rank: string;
}

export interface SafetyScmOverdueSoiArea {
  area_id: number;
  area_name: string | null;
  due_at: string | null;
  message: string;
  overdue_days: number;
}

export interface SafetyScmSubmitPayload {
  device_fingerprint?: string;
  typed_name?: string;
}

export interface SafetyScmOfficeReviewPayload {
  is_reviewed?: boolean;
  office_comment: string;
}

export interface SafetyScmSignatureStatus {
  display_name: string | null;
  required: boolean;
  signed_at: string | null;
  signer_crew_id: string;
  signer_role: 'CO' | 'ATTENDEE' | 'MASTER';
  status: 'SIGNED' | 'NOT_SIGNED' | 'NOT_REQUIRED';
  typed_name: string | null;
}

export interface SafetyScmWrhHostReadiness {
  blocking_crew: Array<{
    crew_id: string;
    display_name: string;
    rank_name: string;
    warning_codes: string[];
    warnings: string[];
    wrh_data_available: boolean;
    wrh_flag: 'GREEN' | 'YELLOW' | 'RED' | 'PENDING';
    wrh_non_compliance_flag: boolean;
  }>;
  checked_crew_count: number;
  message: string;
  missing_ship_time: boolean;
  ready: boolean;
  warnings: string[];
}

export interface SafetyScmFormConfig {
  attendee_rows: SafetyScmCreateAttendeeRow[];
  cadence_warning: {
    days_since_last_regular_closure: number;
    last_regular_closed_at: string;
    message: string;
    severity: string;
  } | null;
  cadence_status: {
    days_since_last_regular_closure: number | null;
    is_overdue: boolean;
    last_regular_closed_at: string | null;
    next_due_date: string | null;
  };
  chair: SafetyScmCrewSnapshot | null;
  closed_since_last: SafetyScmClosedSinceLastPayload;
  generated_at: string;
  latest_circulars?: SafetyScmCircularFeedItem[];
  latest_near_misses?: SafetyScmNearMissFeedItem[];
  latest_psc_cars?: SafetyScmPscCarFeedItem[];
  meeting_date_default: string;
  meeting_type: 'REGULAR' | 'AD_HOC';
  overdue_soi_areas: SafetyScmOverdueSoiArea[];
  prepared_by: SafetyScmCrewSnapshot | null;
  sections: SafetyScmSection[];
  unresolved_previous_actions: SafetyScmCarriedForwardItem[];
  vessel: {
    id: string;
    vessel_code: string;
    vessel_name: string;
  };
  wrh_host_readiness?: SafetyScmWrhHostReadiness;
}

export interface SafetyScmCreatePayload {
  ad_hoc_trigger_reason?: string;
  attendance_rows?: Array<{
    absence_reason?: string | null;
    crew_id: string;
    display_name: string;
    present?: boolean;
    rank_name: string;
    remarks?: string | null;
    schema_version?: number;
  }>;
  chair_crew_id?: string;
  latitude?: string | number | null;
  location?: string;
  longitude?: string | number | null;
  meeting_date: string;
  meeting_time_local: string;
  meeting_type: 'REGULAR' | 'AD_HOC';
  occasion?: string;
  ship_position?: 'S' | 'P';
  ship_pos_from?: string;
  ship_pos_to?: string;
  comm_time?: string;
  comp_time?: string;
  schema_version?: number;
  sections: Array<{
    agenda_item_number: number;
    content: string;
    decision?: string | null;
    legacy_fields?: Record<string, string | number | boolean | null>;
    section_label: string;
  }>;
  vessel_code?: string;
  vessel_id: string;
  voyage_no?: string;
}

export interface SafetySoiCrewSnapshot {
  crew_id: string;
  crew_name?: string;
  department: string;
  rank: string;
  vessel_id: string;
}

export interface SafetySoiSection12Status {
  covered_by_inspection_id: string | null;
  covered_by_inspection_reference: string | null;
  covered_planned_date: string | null;
  covered_this_cycle: boolean;
  cycle_end: string;
  cycle_label: string;
  cycle_start: string;
  next_allowed_date: string | null;
  prompt_required: boolean;
  vessel_id: string;
}

export interface SafetySoiCreateConfigResponse {
  areas: SafetySoiAreaOption[];
  assistant_candidates: SafetySoiCrewSnapshot[];
  checklist_version: SafetySoiInspection['checklist_version'];
  max_trainees: number;
  responsible_candidates: SafetySoiCrewSnapshot[];
  safety_officer: SafetySoiCrewSnapshot | null;
  section_12_status: SafetySoiSection12Status;
  trainee_candidates: SafetySoiCrewSnapshot[];
}

export interface SafetySoiCreatePayload {
  area_ids: number[];
  assistant_crew_id: string;
  cycle_label: string;
  planned_date: string;
  safety_officer_crew_id?: string;
  schema_version?: number;
  section_12_included: boolean;
  trainee_crew_ids?: string[];
  vessel_id: string;
}

export interface SafetySoiPickAreasResponse {
  available_areas: SafetySoiAreaOption[];
  inspection_id: string;
  section_12_included: boolean;
  section_12_status: SafetySoiSection12Status;
  selected_areas: SafetySoiInspectionArea[];
  vessel_id: string;
}

export interface SafetySoiCloseSnapshot {
  checklist_unique_id: string | null;
  closed_at: string | null;
  crew_rotation: {
    accompanied_crew_count: number;
    coverage_percent: number | null;
    crew: Array<{
      crew_id: string;
      inspections_accompanied: number;
    }>;
    display_value: string;
    total_active_crew: number;
    vessel_id: string;
    window_days: number;
    window_end: string;
    window_start: string;
  };
  finding_summary: {
    carried_forward_count: number;
    closed_count: number;
    master_approved_count: number;
    open_count: number;
    pending_closure_count: number;
    total_count: number;
  };
  inspection_id: string;
  inspection_reference: string;
  planned_date: string;
  selected_areas: SafetySoiInspectionArea[];
  signature: {
    device_fingerprint_last8: string;
    signed_at: string;
    signer_display_name: string;
  } | null;
  state: string;
  trainees: SafetySoiTrainee[];
  vessel_id: string;
}

export interface SafetySoiClosePayload {
  device_fingerprint: string;
  typed_name: string;
}

export interface SafetySoiFinding {
  area_id: number;
  assigned_crew_id: string | null;
  carried_forward_count: number;
  closed_at: string | null;
  closure_note: string | null;
  created_by: string | null;
  created_date: string;
  description: string;
  due_date: string | null;
  id: string;
  incident_linked_id: number | null;
  incident_linked_number: string | null;
  incident_worthy_reason: string | null;
  inspection_id: string;
  is_repeat: boolean;
  item_id: number | null;
  life_threat_escalation_target: string | null;
  master_approval_state: string | null;
  master_approved_at: string | null;
  master_approved_by: string | null;
  master_counter_signature: {
    device_fingerprint_last8: string;
    signed_at: string;
    signer_display_name: string;
  } | null;
  mscat_category_id: number | null;
  mscat_subcode_id: string | null;
  pending_closure_signature: {
    device_fingerprint_last8: string;
    signed_at: string;
    signer_display_name: string;
  } | null;
  photo_attachment_path: string | null;
  priority: 'HIGH' | 'MED' | 'LOW';
  proposed_action: string | null;
  repeat_badge_text: string | null;
  repeat_occurrence_count: number;
  schema_version: number;
  severity: 'HIGH' | 'MED' | 'LOW';
  shell_tag: string | null;
  status: string;
  title: string;
  updated_by: string | null;
  updated_date: string;
}

export interface SafetySoiFindingCreatePayload {
  area_id: number;
  assigned_crew_id?: string | null;
  checklist_unique_id: string;
  description: string;
  due_date?: string | null;
  incident_worthy_action?: 'CREATE_INCIDENT' | 'KEEP_SOI_ONLY' | null;
  incident_worthy_reason?: string | null;
  item_id?: number | null;
  life_threat_escalation_target?: 'INCIDENT' | 'NEAR_MISS' | null;
  mscat_category_id?: number | null;
  mscat_subcode_id?: string | null;
  photo_attachment_path?: string | null;
  priority: 'HIGH' | 'MED' | 'LOW';
  proposed_action?: string | null;
  severity: 'HIGH' | 'MED' | 'LOW';
  shell_tag?: string | null;
  title: string;
}

export interface SafetySoiFindingCreateResponse extends SafetySoiFinding {
  high_severity_nudge?: Record<string, unknown>;
}

export interface SafetySoiPhotoUploadResponse {
  byte_size: number;
  content_type: string;
  file_name: string;
  photo_attachment_path: string;
}

export interface SafetySoiFindingSubmitResponse {
  checklist_unique_id: string | null;
  inspection_id: string;
  pdf_export?: {
    download_path: string;
    export_path: string;
    file_name: string;
  };
  remaining_area_ids: number[];
  reported_at: string | null;
  state: string;
  submitted_area_ids: number[];
  total_selected_area_count: number;
}

export interface SafetySoiFindingPendingClosurePayload {
  closure_note?: string | null;
  device_fingerprint: string;
  typed_name: string;
}

export interface SafetySoiFindingReopenPayload {
  reason: string;
}

export interface SafetySoiFindingApprovalPayload {
  closure_note?: string | null;
  decision: 'APPROVE' | 'REJECT';
  device_fingerprint?: string | null;
  reason?: string | null;
  typed_name?: string | null;
}

export interface SafetySoiFindingActionResponse extends SafetySoiFinding {
  transition?: Record<string, unknown>;
}

export interface SafetySoiApplicabilityRequestScreen {
  areas: SafetySoiAreaOption[];
  inspection_id: string;
  inspection_reference: string;
  vessel_id: string;
}

export interface SafetySoiApplicabilityRequestPayload {
  area_id: number;
  master_signature: string;
  new_applicable: boolean;
  reason: string;
}

export interface SafetySoiApplicabilityRequestResult {
  area_id: number;
  area_name: string | null;
  current_applicable: boolean;
  master_requested_at: string | null;
  master_requested_by: string;
  reason: string;
  request_id: string;
  requested_applicable: boolean;
  status: string;
  vessel_id: string;
}

export interface SafetySoiApplicabilityApprovalScreen {
  inspection_id: string;
  inspection_reference: string;
  pending_requests: Array<{
    area_id: number;
    area_name: string;
    master_requested_at: string;
    master_requested_by: string;
    master_signature: string;
    new_applicable: boolean;
    old_applicable: boolean;
    reason: string;
    request_id: string;
    section_12_flag: boolean;
    vessel_id: string;
  }>;
  vessel_id: string;
}

export interface SafetySoiApplicabilityApprovalPayload {
  area_id: number;
  dpa_decision: 'APPROVED' | 'REJECTED';
  dpa_signature: string;
  reason: string;
}

export interface SafetySoiApplicabilityApprovalResult {
  applicable: boolean;
  area_id: number;
  area_name: string | null;
  current_applicable: boolean;
  decision: string;
  dpa_approved_at: string | null;
  dpa_approved_by: string;
  map_id: string | null;
  reason: string;
  request_id: string;
  requested_applicable: boolean;
  status: string;
  vessel_id: string;
}

export interface SafetySoiComplianceArea {
  amber_status: boolean;
  area_id: number;
  area_name: string;
  due_at: string | null;
  is_overdue: boolean;
  last_inspected_at: string | null;
  section_12_flag: boolean;
  status_label: string;
}

export interface SafetySoiAreaOption {
  applicable: boolean;
  area_id: number;
  area_name: string;
  due_at: string | null;
  last_inspected_at: string | null;
  map_id: string | null;
  schema_version: number;
  section_12_flag: boolean;
}

export interface SafetySoiComplianceResponse {
  amber_area_count: number;
  applicable_area_count: number;
  areas: SafetySoiComplianceArea[];
  calculated_at: string;
  compliance_percent: number | null;
  display_value: string;
  inspected_area_count: number;
  label: string;
  overdue_area_count: number;
  status: string;
  vessel_id: string;
}

export interface SafetySoiInspectionArea {
  area_id: number;
  area_name: string;
  display_order: number;
  inspected: boolean;
  inspection_id: string;
  last_inspected_at: string | null;
  notes: string | null;
  schema_version: number;
  section_12_flag: boolean;
  selection_id: string;
}

export interface SafetySoiTrainee {
  crew_id: string;
  inspection_id: string;
  schema_version: number;
  trainee_slot: number;
}

export interface SafetySoiInspection {
  assistant_crew_id: string;
  assistant_department: string;
  checklist_format: string | null;
  checklist_generated_at: string | null;
  checklist_unique_id: string | null;
  checklist_version: {
    active: boolean;
    effective_from: string;
    effective_to: string | null;
    id: string;
    source_description: string;
    version_label: string;
  } | null;
  closed_at: string | null;
  created_by: string | null;
  created_date: string;
  cycle_label: string;
  fieldwork_started_at: string | null;
  id: string;
  inspection_reference: string;
  lost_paper_flag: boolean;
  lost_paper_note: string | null;
  master_crew_id: string | null;
  planned_date: string;
  reported_at: string | null;
  safety_officer_crew_id: string;
  safety_officer_department: string;
  schema_version: number;
  section_12_included: boolean;
  selected_areas: SafetySoiInspectionArea[];
  state: string;
  trainees: SafetySoiTrainee[];
  updated_by: string | null;
  updated_date: string;
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_id: string;
  vessel_name?: string | null;
}

export interface SafetySoiOfficerSetting {
  alternate_candidates: Array<{
    crew_id: string;
    crew_name?: string;
    department: string;
    rank: string;
    vessel_id: string;
  }>;
  alternate_enabled: boolean;
  alternate_so_crew_id: string | null;
  disabled_at: string | null;
  disabled_by: string | null;
  enabled_at: string | null;
  enabled_by: string | null;
  id: string;
  message?: string;
  migration_required?: boolean;
  reason: string | null;
  vessel_id: string;
}

export interface SafetySoiOfficerSettingPayload {
  alternate_enabled: boolean;
  alternate_so_crew_id?: string | null;
  reason?: string | null;
}

export type SafetySearchGroupKey =
  | 'INCIDENT'
  | 'NEAR_MISS'
  | 'SCM'
  | 'SOI_FINDING';

export interface SafetySearchResultItem {
  archived: boolean;
  id: string;
  inspection_id?: number;
  near_miss_priority?: string | null;
  record_label: string;
  record_type: SafetySearchGroupKey;
  reference: string;
  reporter_name?: string | null;
  route: string;
  snippet: string;
  state: string;
  title: string;
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_id: string;
  vessel_name?: string | null;
  when: string | null;
}

export interface SafetySearchResponse {
  counts: Record<SafetySearchGroupKey, number>;
  groups: Record<SafetySearchGroupKey, SafetySearchResultItem[]>;
  include_archived: boolean;
  labels: Record<SafetySearchGroupKey, string>;
  query: string;
  record_type: string;
  total_count: number;
}

export interface SafetyDashboardExportRequest {
  format: 'excel' | 'pdf' | 'xlsx';
  period: SafetyDashboardPeriodCode;
  vessel_id?: string | null;
}

export interface SafetyDashboardExportResult {
  blob: Blob;
  fileName: string;
}

export type SafetyOfficeWorkflowPayload = Record<string, unknown>;
export type SafetyOfficeWorkflowResponse = Record<string, unknown>;

export interface SafetyIncidentPhase4EvidenceSource {
  detail: string;
  id: string;
  label: string;
  source_type: string;
  tab_code?: string;
}

export interface SafetyIncidentPhase4Gate {
  blockers: string[];
  can_continue: boolean;
  covered_tabs: string[];
  facts_count: number;
  missing_tabs: string[];
}

export interface SafetyDownloadResult {
  blob: Blob;
  fileName: string;
}

export interface SafetyAuditorBundleExportRequest {
  date_from: string;
  date_to: string;
  record_types: string[];
  vessel_id?: string | null;
}

export interface SafetyIncidentFilters {
  date_from?: string;
  date_to?: string;
  record_type?: 'INCIDENT' | 'NEAR_MISS';
  risk_band?: string;
  state?: string;
  vessel_id?: string;
}

export interface SafetyIncidentCreatePayload {
  awaiting_daily_report_match?: boolean;
  external_party_injury?: Record<string, unknown> | null;
  incident_type_id?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  shore_assistance_required?: boolean | null;
  vessel_location?: string;
  onboard_location?: string;
  last_port?: string;
  departure_date?: string | null;
  vessel_condition?: 'LOADED' | 'BALLAST' | '' | null;
  loss_type_primary_id?: number | null;
  loss_type_secondary_id?: number | null;
  loss_type_tertiary_id?: number | null;
  loss_type_other?: string | null;
  narrative?: string;
  occurred_at?: string | null;
  office_notification_mode?: 'ON_CALL' | 'WHATSAPP' | 'EMAIL' | null;
  office_notified?: boolean | null;
  pic_candidate_id?: string;
  position_daily_report_id?: string | null;
  position_source?: string | null;
  weather_visibility_id?: string | null;
  weather_precipitation_id?: string | null;
  weather_sea_state_id?: string | null;
  weather_wind_scale_id?: string | null;
  weather_wind_direction_id?: string | null;
  weather_lighting_source_id?: string | null;
  weather_current_direction_id?: string | null;
  weather_current_strength_knots?: string | null;
  weather_ambient_temperature_c?: string | null;
  weather_ice_condition_onboard_id?: string | null;
  weather_ice_condition_at_sea_id?: string | null;
  weather_light_condition_id?: string | null;
  record_type?: 'INCIDENT' | 'NEAR_MISS';
  reported_at?: string | null;
  reporter_department?: string;
  reporter_device_fingerprint?: string;
  reporter_name?: string;
  reporter_rank?: string;
  reporter_user_id?: string;
  risk_band?: 'GREEN' | 'YELLOW' | 'RED';
  schema_version?: number;
  vessel_code?: string;
  vessel_id?: string;
}

export interface SafetyIncidentPhase1Record
  extends Omit<
    SafetyIncidentCreatePayload,
    'external_party_injury' | 'reporter_user_id' | 'risk_band'
  > {
  created_by?: string | null;
  created_date?: string;
  current_phase?: number;
  external_party_injury?: Record<string, unknown> | null;
  id: string;
  incident_number?: string | null;
  record_type?: 'INCIDENT';
  reporter_email?: string | null;
  reporter_user_id?: string | null;
  risk_band?: 'GREEN' | 'YELLOW' | 'RED' | null;
  state?: string;
  updated_by?: string | null;
  updated_date?: string;
  vessel_display_name?: string | null;
  vessel_name?: string | null;
}

export interface SafetyIncidentPhase1SubmitPayload {
  conflict_acknowledged?: boolean;
  conflict_approver_role?: 'MASTER' | 'DPA';
  injured_party_id?: string;
  person_in_charge_id?: string;
  pic_candidate_id?: string;
}

export interface SafetyIncidentPhase2Payload {
  dpa_notified_at?: string | null;
  fm_notified_at?: string | null;
  imo_classifier?: 'SMC' | 'MC' | 'MI' | 'NOT_APPLICABLE';
  investigation_depth?: 'SHALLOW' | 'MEDIUM' | 'DEEP' | null;
  latitude?: string;
  longitude?: string;
  loss_type_primary_id?: number | null;
  loss_type_secondary_id?: number | null;
  loss_type_tertiary_id?: number | null;
  loss_type_other?: string | null;
  office_notified_at?: string | null;
  office_notification_mode?: 'ON_CALL' | 'WHATSAPP' | 'EMAIL' | null;
  office_notified?: boolean | null;
  pic_user_id?: string | null;
  risk_band?: 'GREEN' | 'YELLOW' | 'RED';
  schema_version?: number;
}

export interface SafetyIncidentPhase2Record
  extends SafetyIncidentPhase2Payload {
  advisory_band: 'GREEN' | 'YELLOW' | 'RED';
  created_by: string | null;
  created_date: string;
  current_phase: number;
  draft_reference: string | null;
  id: string;
  incident_number: string | null;
  notification_channel_count: number;
  resources_allocated: string | null;
  state: string;
  updated_by: string | null;
  updated_date: string | null;
}

export interface SafetyIncidentPhase2SubmitResponse
  extends SafetyIncidentPhase2Record {
  deadline_tasks_created: number;
  notifications_emitted: number;
  transition: {
    incident_id: number;
    occurred_at: string;
    phase_from: number | null;
    phase_to: number;
    transition_type: string;
  };
}

export interface SafetyNearMissFilters {
  date_from?: string;
  date_to?: string;
  priority?: string;
  state?: string;
  vessel_id?: string;
}

export interface SafetyNearMissRateLimitStatus {
  allowed: boolean;
  guidance_message: string | null;
  limit: number | null;
  remaining: number | null;
  reset_at: string | null;
  retry_after_seconds: number;
  scope: string;
  used: number;
}

export interface SafetyNearMissCreatePayload {
  incident_type_id: number;
  loss_type_primary_id: number;
  narrative: string;
  high_severity_photo_file?: File | null;
  near_miss_immediate_action: string;
  near_miss_place?: 'AT_ANCHOR' | 'AT_SEA' | 'AT_PORT' | null;
  near_miss_category_tags?: string[];
  near_miss_incident_type_ids?: number[];
  near_miss_mscat_category_id?: number | null;
  near_miss_mscat_subcode_id?: string | null;
  near_miss_mscat_subcode_ids?: string[];
  near_miss_factor_causes?: Array<{
    factor: 'HUMAN' | 'VESSEL' | 'MANAGEMENT' | 'OTHER';
    immediate_option_id: string;
    immediate_option_text?: string;
    immediate_other_text?: string;
    root_option_id: string;
    root_option_text?: string;
    root_other_text?: string;
  }>;
  near_miss_severity: 'HIGH' | 'MED' | 'LOW';
  near_miss_shell_tag?: string | null;
  near_miss_suggestion?: string;
  near_miss_root_cause_detail?: string;
  near_miss_corrective_action?: string;
  near_miss_weather_voyage_details?: string;
  near_miss_equipment_details?: string;
  near_miss_lessons_learned?: string;
  occurred_at?: string | null;
  reported_at?: string | null;
  reporter_device_fingerprint?: string;
  reporter_name?: string;
  reporter_rank?: string;
  reporter_user_id?: string;
  schema_version?: number;
  vessel_code?: string;
  vessel_id?: string;
}

export interface SafetyNearMissGuidancePrompt {
  id: string;
  category_tag: string | null;
  incident_type_id: number | null;
  prompt_text: string;
  display_order: number;
  active: boolean;
}

export interface SafetyNearMissKpiTarget {
  id: string | null;
  vessel_id: string;
  year: number;
  month: number;
  target_count: number;
  actual_count: number;
  variance: number;
  active: boolean;
}

export interface SafetyScmFilters {
  date_from?: string;
  date_to?: string;
  meeting_type?: string;
  state?: string;
  vessel_id?: string;
}

export interface SafetySoiFilters {
  cycle_label?: string;
  date_from?: string;
  date_to?: string;
  state?: string;
  vessel_id?: string;
}

function extractFileName(
  contentDisposition: string | undefined,
  fallback: string
): string {
  const match = contentDisposition?.match(/filename="?([^"]+)"?/i);
  return match?.[1] ?? fallback;
}

export const safetyApi = {
  async getReferenceMscat() {
    const response = await apiClient.get<SafetyReferenceMscatOption[]>(
      buildSafetyApiUrl('/reference/mscat/')
    );
    return response.data;
  },

  async getReferenceImmediateCauses() {
    const response = await apiClient.get<SafetyReferenceImmediateCauseOption[]>(
      buildSafetyApiUrl('/reference/immediate-causes/')
    );
    return response.data;
  },

  async getNearMissCauseOptions() {
    const response = await apiClient.get<
      SafetyNearMissCauseOption[] | PaginatedResponse<SafetyNearMissCauseOption>
    >(buildSafetyApiUrl('/near-miss/cause-options/'), {
      params: { page_size: 500 },
    });
    return unwrapPaginatedResults(response.data);
  },

  async getNearMissCategories() {
    const response = await apiClient.get<
      | SafetyNearMissCategoryOption[]
      | PaginatedResponse<SafetyNearMissCategoryOption>
    >(buildSafetyApiUrl('/near-miss/categories/'), {
      params: { page_size: 100 },
    });
    return unwrapPaginatedResults(response.data);
  },

  async getReferenceLossTypes() {
    const response = await apiClient.get<SafetyReferenceLossTypeOption[]>(
      buildSafetyApiUrl('/reference/loss-types/')
    );
    return response.data;
  },

  async getReferenceIncidentTypes() {
    const response = await apiClient.get<SafetyReferenceIncidentTypeOption[]>(
      buildSafetyApiUrl('/reference/incident-types/')
    );
    return response.data;
  },

  async getIncidentWeatherOptions(fieldKey?: SafetyIncidentWeatherFieldKey) {
    const response = await apiClient.get<
      | SafetyIncidentWeatherOption[]
      | PaginatedResponse<SafetyIncidentWeatherOption>
    >(buildSafetyApiUrl('/reference/incident-weather-options/'), {
      params: buildParams({ field_key: fieldKey }),
    });
    return unwrapPaginatedResults(response.data);
  },

  async getInjuryDropdownOptions(fieldKey?: SafetyInjuryDropdownFieldKey) {
    const response = await apiClient.get<
      | SafetyInjuryDropdownOption[]
      | PaginatedResponse<SafetyInjuryDropdownOption>
    >(buildSafetyApiUrl('/reference/injury-dropdown-options/'), {
      params: buildParams({ field_key: fieldKey }),
    });
    return unwrapPaginatedResults(response.data);
  },

  async getReferenceSoiAreas() {
    const response = await apiClient.get<SafetyReferenceSoiAreaOption[]>(
      buildSafetyApiUrl('/reference/soi-areas/')
    );
    return response.data;
  },

  async getReferenceSoiItems(areaId?: number | null) {
    const response = await apiClient.get<SafetyReferenceSoiItemOption[]>(
      buildSafetyApiUrl('/reference/soi-items/'),
      {
        params: buildParams({ area_id: areaId }),
      }
    );
    return response.data;
  },

  async getReferenceSoiChecklistVersions() {
    const response = await apiClient.get<
      SafetyReferenceChecklistVersionOption[]
    >(buildSafetyApiUrl('/reference/soi-checklist-versions/'));
    return response.data;
  },

  async getReferenceBiasGuards() {
    const response = await apiClient.get<SafetyReferenceBiasGuardOption[]>(
      buildSafetyApiUrl('/reference/bias-guards/')
    );
    return response.data;
  },

  async getDashboardComposite(
    period: SafetyDashboardPeriodCode,
    vesselId?: string | null
  ) {
    const response = await apiClient.get<SafetyDashboardCompositeResponse>(
      buildSafetyApiUrl('/dashboard/composite/'),
      {
        params: buildParams({ period, vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async getDashboardHeinrich(vesselId?: string | null) {
    const response = await apiClient.get<SafetyDashboardHeinrichResponse>(
      buildSafetyApiUrl('/dashboard/heinrich/'),
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async getDashboardRepeatRoot(vesselId?: string | null) {
    const response =
      await apiClient.get<SafetyDashboardRepeatRootRadarResponse>(
        buildSafetyApiUrl('/dashboard/repeat-root-cause/'),
        {
          params: buildParams({ vessel_id: vesselId }),
        }
      );
    return response.data;
  },

  async getDashboardPareto(vesselId?: string | null) {
    const response = await apiClient.get<SafetyDashboardParetoResponse>(
      buildSafetyApiUrl('/dashboard/pareto/'),
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async getDashboardSoiCompliance(vesselId?: string | null) {
    const response = await apiClient.get<SafetyDashboardSoiComplianceResponse>(
      buildSafetyApiUrl('/dashboard/soi-compliance/'),
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async getDashboardCaAging(vesselId?: string | null) {
    const response = await apiClient.get<SafetyDashboardCaAgingResponse>(
      buildSafetyApiUrl('/dashboard/ca-aging/'),
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async exportDashboard(
    request: SafetyDashboardExportRequest
  ): Promise<SafetyDashboardExportResult> {
    const response = await apiClient.post<Blob>(
      buildSafetyApiUrl('/dashboard/export/'),
      request,
      {
        responseType: 'blob',
      }
    );
    return {
      blob: response.data,
      fileName: extractFileName(
        response.headers['content-disposition'],
        `safety-dashboard-${request.period}.${request.format === 'pdf' ? 'pdf' : 'xlsx'}`
      ),
    };
  },

  async getIncidents(filters: SafetyIncidentFilters = {}) {
    const response = await apiClient.get<
      SafetyIncidentListItem[] | PaginatedResponse<SafetyIncidentListItem>
    >(buildSafetyApiUrl('/incidents/'), {
      params: buildParams(filters),
    });
    return unwrapPaginatedResults(response.data);
  },

  async createIncident(payload: SafetyIncidentCreatePayload) {
    const response = await apiClient.post<SafetyIncidentListItem>(
      buildSafetyApiUrl('/incidents/'),
      payload
    );
    return response.data;
  },

  async getIncidentPhase1(id: number | string) {
    const response = await apiClient.get<SafetyIncidentPhase1Record>(
      buildSafetyApiUrl(`/incidents/${id}/phase-1/`)
    );
    return response.data;
  },

  async updateIncidentPhase1(
    id: number | string,
    payload: SafetyIncidentCreatePayload
  ) {
    const response = await apiClient.patch<SafetyIncidentPhase1Record>(
      buildSafetyApiUrl(`/incidents/${id}/phase-1/`),
      payload
    );
    return response.data;
  },

  async submitIncidentPhase1(
    id: number | string,
    payload: SafetyIncidentPhase1SubmitPayload = {}
  ) {
    const response = await apiClient.post<
      SafetyIncidentListItem & {
        phase_2_handoff: {
          authorized_roles: string[];
          can_edit_phase_2: boolean;
          message: string;
          notifications_emitted: number;
        };
        transition: {
          incident_id: number;
          occurred_at: string;
          phase_from: number | null;
          phase_to: number;
          transition_type: string;
        };
        self_report_conflict: {
          conflict_detected: boolean;
          message: string;
          required_approver_role: string | null;
        };
      }
    >(buildSafetyApiUrl(`/incidents/${id}/phase-1/submit/`), payload);
    return response.data;
  },

  async getIncidentPhase2(id: number | string) {
    const response = await apiClient.get<SafetyIncidentPhase2Record>(
      buildSafetyApiUrl(`/incidents/${id}/resource-handoff/`)
    );
    return response.data;
  },

  async updateIncidentPhase2(
    id: number | string,
    payload: SafetyIncidentPhase2Payload
  ) {
    const response = await apiClient.patch<SafetyIncidentPhase2Record>(
      buildSafetyApiUrl(`/incidents/${id}/resource-handoff/`),
      payload
    );
    return response.data;
  },

  async submitIncidentPhase2(id: number | string) {
    const response = await apiClient.post<SafetyIncidentPhase2SubmitResponse>(
      buildSafetyApiUrl(`/incidents/${id}/resource-handoff/submit/`),
      {}
    );
    return response.data;
  },

  async getIncidentPhase3Evidence(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/evidence/`)
    );
    return response.data;
  },

  async updateIncidentPhase3Evidence(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/evidence/`),
      payload
    );
    return response.data;
  },

  async uploadIncidentPhase3Attachment(
    id: number | string,
    tabKey: string,
    file: File,
    metadata?: { description?: string; title?: string }
  ) {
    const formData = new FormData();
    formData.append('tab_key', tabKey);
    formData.append('file', file);
    if (metadata?.title) {
      formData.append('title', metadata.title);
    }
    if (metadata?.description) {
      formData.append('description', metadata.description);
    }
    const response = await apiClient.post<{
      attachment: SafetyOfficeWorkflowResponse;
      workspace: SafetyOfficeWorkflowResponse;
    }>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/evidence/attachments/`),
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  async getIncidentPhase3AttachmentBlob(
    id: number | string,
    attachmentPath: string
  ) {
    const response = await apiClient.get<Blob>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/evidence/attachments/`),
      {
        params: { path: attachmentPath },
        responseType: 'blob',
      }
    );
    return response.data;
  },

  getIncidentPhase3AttachmentPreviewUrl(
    id: number | string,
    attachmentPath: string
  ) {
    const params = new URLSearchParams({ path: attachmentPath });
    return `${buildSafetyApiUrl(`/incidents/${id}/phase-4/evidence/attachments/`)}?${params.toString()}`;
  },

  async deleteIncidentPhase3Attachment(
    id: number | string,
    attachmentPath: string
  ) {
    const response = await apiClient.delete<{
      workspace: SafetyOfficeWorkflowResponse;
    }>(buildSafetyApiUrl(`/incidents/${id}/phase-4/evidence/attachments/`), {
      params: { path: attachmentPath },
    });
    return response.data;
  },

  async updateIncidentPhase3AttachmentMetadata(
    id: number | string,
    attachmentPath: string,
    payload: { description?: string; title: string }
  ) {
    const response = await apiClient.patch<{
      attachment: SafetyOfficeWorkflowResponse;
      workspace: SafetyOfficeWorkflowResponse;
    }>(buildSafetyApiUrl(`/incidents/${id}/phase-4/evidence/attachments/`), payload, {
      params: { path: attachmentPath },
    });
    return response.data;
  },

  async getIncidentPhase3ChainOfCustody(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse[]>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/chain-of-custody/`)
    );
    return response.data;
  },

  async createIncidentPhase3ChainOfCustody(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/chain-of-custody/`),
      payload
    );
    return response.data;
  },

  async getIncidentPhase3EvidenceMatrix(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse[]>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/evidence-matrix/`)
    );
    return response.data;
  },

  async createIncidentPhase3EvidenceMatrixRow(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/evidence-matrix/`),
      payload
    );
    return response.data;
  },

  async getIncidentPhase3Interviews(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse[]>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/interviews/`)
    );
    return response.data;
  },

  async createIncidentPhase3Interview(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/interviews/`),
      payload
    );
    return response.data;
  },

  async updateIncidentPhase3Interview(
    id: number | string,
    interviewId: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/interviews/${interviewId}/`),
      payload
    );
    return response.data;
  },

  async updateIncidentPhase3DeadlineTask(
    id: number | string,
    taskId: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(
        `/incidents/${id}/phase-4/evidence/deadline-tasks/${taskId}/`
      ),
      payload
    );
    return response.data;
  },

  async getIncidentPhase4Facts(id: number | string) {
    const response = await apiClient.get<
      | SafetyOfficeWorkflowResponse[]
      | PaginatedResponse<SafetyOfficeWorkflowResponse>
    >(buildSafetyApiUrl(`/incidents/${id}/phase-4/facts/`));
    return unwrapPaginatedResults(response.data);
  },

  async getIncidentPhase4EvidenceSources(id: number | string) {
    const response = await apiClient.get<SafetyIncidentPhase4EvidenceSource[]>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/facts/sources/`)
    );
    return response.data;
  },

  async getIncidentPhase4Gate(id: number | string) {
    const response = await apiClient.get<SafetyIncidentPhase4Gate>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/facts/gate/`)
    );
    return response.data;
  },

  async transitionIncident(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/transition/`),
      payload
    );
    return response.data;
  },

  async createIncidentPhase4Fact(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/facts/`),
      payload
    );
    return response.data;
  },

  async updateIncidentPhase4Fact(
    id: number | string,
    factId: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/facts/${factId}/`),
      payload
    );
    return response.data;
  },

  async reorderIncidentPhase4Facts(
    id: number | string,
    orderedFactIds: Array<number | string>
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse[]>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/facts/reorder/`),
      { ordered_fact_ids: orderedFactIds }
    );
    return response.data;
  },

  async setIncidentPhase4FactContradiction(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-4/facts/contradictions/`),
      payload
    );
    return response.data;
  },

  async getIncidentPhase5Workspace(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-2/analysis/`)
    );
    return response.data;
  },

  async updateIncidentPhase5Workspace(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-2/analysis/`),
      payload
    );
    return response.data;
  },

  async searchIncidentMscat(id: number | string, query: string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-2/analysis/mscat/`),
      {
        params: buildParams({ q: query }),
      }
    );
    return response.data;
  },

  async createIncidentPhase5Cause(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-2/analysis/causes/`),
      payload
    );
    return response.data;
  },

  async updateIncidentPhase5Cause(
    id: number | string,
    causeId: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-2/analysis/causes/${causeId}/`),
      payload
    );
    return response.data;
  },

  async createIncidentPhase5Safeguard(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-2/analysis/safeguards/`),
      payload
    );
    return response.data;
  },

  async updateIncidentPhase5Safeguard(
    id: number | string,
    safeguardId: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(
        `/incidents/${id}/phase-2/analysis/safeguards/${safeguardId}/`
      ),
      payload
    );
    return response.data;
  },

  async getIncidentBiasGuards(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse[]>(
      buildSafetyApiUrl(`/incidents/${id}/phase-2/bias-guards/`)
    );
    return response.data;
  },

  async submitIncidentBiasGuards(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse[]>(
      buildSafetyApiUrl(`/incidents/${id}/phase-2/bias-guards/`),
      payload
    );
    return response.data;
  },

  async overrideIncidentBlameGuard(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-2/override-blame/`),
      payload
    );
    return response.data;
  },

  async getIncidentPhase6Workspace(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-3/`)
    );
    return response.data;
  },

  async getIncidentRecommendations(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-3/recommendations/`)
    );
    return response.data;
  },

  async createIncidentRecommendation(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-3/recommendations/`),
      payload
    );
    return response.data;
  },

  async updateIncidentRecommendation(
    id: number | string,
    recommendationId: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(
        `/incidents/${id}/phase-3/recommendations/${recommendationId}/`
      ),
      payload
    );
    return response.data;
  },

  async getIncidentPhase7Preflight(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-5/preflight/`)
    );
    return response.data;
  },

  async acceptIncidentPhase7(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-5/accept/`),
      payload
    );
    return response.data;
  },

  async signIncidentPhase7Hod(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-5/hod-signature/`),
      payload
    );
    return response.data;
  },

  async approveRedIncidentPhase7(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-5/approve-red/`),
      payload
    );
    return response.data;
  },

  async sendBackIncidentPhase7(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-5/send-back/`),
      payload
    );
    return response.data;
  },

  async getIncidentPhase8Workspace(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-6/`)
    );
    return response.data;
  },

  async saveIncidentPhase8LossEvaluation(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-6/`),
      payload
    );
    return response.data;
  },

  async verifyIncidentPhase8(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-6/verify/`),
      payload
    );
    return response.data;
  },

  async closeIncidentPhase8(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-6/close/`),
      payload
    );
    return response.data;
  },

  async getIncidentClosureSummary(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/phase-7/closure/`)
    );
    return response.data;
  },

  async getIncidentAudit(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/audit/`)
    );
    return response.data;
  },

  async reopenIncident(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/incidents/${id}/reopen/`),
      payload
    );
    return response.data;
  },

  async downloadIncidentPdf(
    id: number | string,
    sections?: readonly string[]
  ): Promise<SafetyDownloadResult> {
    const params = sections?.length
      ? { sections: sections.join(',') }
      : undefined;
    const response = await apiClient.get<Blob>(
      buildSafetyApiUrl(`/export/incident/${id}/pdf/`),
      { params, responseType: 'blob' }
    );
    return {
      blob: response.data,
      fileName: extractFileName(
        response.headers['content-disposition'],
        `incident-${id}.pdf`
      ),
    };
  },

  async downloadIncidentMscMepc3(
    id: number | string
  ): Promise<SafetyDownloadResult> {
    const response = await apiClient.get<Blob>(
      buildSafetyApiUrl(`/export/msc-mepc-3/${id}/`),
      { responseType: 'blob' }
    );
    return {
      blob: response.data,
      fileName: extractFileName(
        response.headers['content-disposition'],
        `incident-${id}-msc-mepc3.pdf`
      ),
    };
  },

  async getCorrectiveActions(
    filters: Record<string, string | number | boolean | null | undefined> = {}
  ) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse[]>(
      buildSafetyApiUrl('/corrective-actions/'),
      {
        params: buildParams(filters),
      }
    );
    return response.data;
  },

  async createCorrectiveAction(payload: SafetyOfficeWorkflowPayload) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl('/corrective-actions/'),
      payload
    );
    return response.data;
  },

  async updateCorrectiveAction(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/corrective-actions/${id}/`),
      payload
    );
    return response.data;
  },

  async transitionCorrectiveAction(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/corrective-actions/${id}/transition/`),
      payload
    );
    return response.data;
  },

  async verifyCorrectiveAction(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/corrective-actions/${id}/verify/`),
      payload
    );
    return response.data;
  },

  async getNearMisses(filters: SafetyNearMissFilters = {}) {
    const response = await apiClient.get<
      SafetyNearMissListItem[] | PaginatedResponse<SafetyNearMissListItem>
    >(buildSafetyApiUrl('/near-miss/'), {
      params: buildParams(filters),
    });
    return unwrapPaginatedResults(response.data);
  },

  async getNearMissRateLimit(filters: { vessel_id?: string } = {}) {
    const response = await apiClient.get<SafetyNearMissRateLimitStatus>(
      buildSafetyApiUrl('/near-miss/rate-limit/'),
      {
        params: buildParams(filters),
      }
    );
    return response.data;
  },

  async getNearMissGuidancePrompts(
    filters: {
      category_tag?: string | null;
      incident_type_id?: number | null;
    } = {}
  ) {
    const response = await apiClient.get<
      | SafetyNearMissGuidancePrompt[]
      | PaginatedResponse<SafetyNearMissGuidancePrompt>
    >(buildSafetyApiUrl('/near-miss/guidance-prompts/'), {
      params: buildParams(
        filters as Record<string, string | number | boolean | null | undefined>
      ),
    });
    return unwrapPaginatedResults(response.data);
  },

  async getNearMissKpiTarget(filters: {
    vessel_id: string;
    year?: number;
    month?: number;
  }) {
    const response = await apiClient.get<SafetyNearMissKpiTarget>(
      buildSafetyApiUrl('/near-miss/kpi-target/'),
      {
        params: buildParams(filters),
      }
    );
    return response.data;
  },

  async saveNearMissKpiTarget(payload: {
    vessel_id: string;
    year: number;
    month: number;
    target_count: number;
  }) {
    const response = await apiClient.post<SafetyNearMissKpiTarget>(
      buildSafetyApiUrl('/near-miss/kpi-target/'),
      payload
    );
    return response.data;
  },

  async createNearMiss(payload: SafetyNearMissCreatePayload) {
    const {
      high_severity_photo_file: highSeverityPhotoFile,
      ...nearMissPayload
    } = payload;
    if (typeof File !== 'undefined' && highSeverityPhotoFile instanceof File) {
      const formData = new FormData();
      formData.append('payload', JSON.stringify(nearMissPayload));
      formData.append('photo', highSeverityPhotoFile);
      const response = await apiClient.post<SafetyNearMissListItem>(
        buildSafetyApiUrl('/near-miss/'),
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      return response.data;
    }
    const response = await apiClient.post<SafetyNearMissListItem>(
      buildSafetyApiUrl('/near-miss/'),
      nearMissPayload
    );
    return response.data;
  },

  async getNearMiss(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/`)
    );
    return response.data;
  },

  async triageNearMiss(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/office-comments/`),
      payload
    );
    return response.data;
  },

  async reclassifyNearMiss(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/reclassify/`),
      payload
    );
    return response.data;
  },

  async reviewNearMiss(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/review/`),
      payload
    );
    return response.data;
  },

  async resubmitNearMissRework(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/rework/`),
      payload
    );
    return response.data;
  },

  async getNearMissAnalysis(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/analysis/`)
    );
    return response.data;
  },

  async createNearMissAnalysisEvidence(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const photoFile = payload.photo_file;
    if (typeof File !== 'undefined' && photoFile instanceof File) {
      const formData = new FormData();
      Object.entries(payload).forEach(([key, value]) => {
        if (key === 'photo_file' || value === undefined || value === null) {
          return;
        }
        formData.append(key, String(value));
      });
      formData.append('photo', photoFile);
      const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
        buildSafetyApiUrl(`/near-miss/${id}/analysis/evidence/`),
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      return response.data;
    }
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/analysis/evidence/`),
      payload
    );
    return response.data;
  },

  async createNearMissAnalysisFact(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/analysis/facts/`),
      payload
    );
    return response.data;
  },

  async updateNearMissAnalysisFact(
    id: number | string,
    factId: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.patch<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/analysis/facts/${factId}/`),
      payload
    );
    return response.data;
  },

  async deleteNearMissAnalysisFact(
    id: number | string,
    factId: number | string
  ) {
    await apiClient.delete(
      buildSafetyApiUrl(`/near-miss/${id}/analysis/facts/${factId}/`)
    );
  },

  async getNearMissFleetAlert(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/fleet-alert/`)
    );
    return response.data;
  },

  async issueNearMissFleetAlert(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/fleet-alert/`),
      payload
    );
    return response.data;
  },

  async getNearMissClosureSummary(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/closure/`)
    );
    return response.data;
  },

  async closeNearMiss(
    id: number | string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    const response = await apiClient.post<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/closure/`),
      payload
    );
    return response.data;
  },

  async getNearMissAudit(id: number | string) {
    const response = await apiClient.get<SafetyOfficeWorkflowResponse>(
      buildSafetyApiUrl(`/near-miss/${id}/audit/`)
    );
    return response.data;
  },

  async downloadNearMissPdf(
    id: number | string
  ): Promise<SafetyDownloadResult> {
    const response = await apiClient.get<Blob>(
      buildSafetyApiUrl(`/near-miss/${id}/pdf/`),
      { responseType: 'blob' }
    );
    return {
      blob: response.data,
      fileName: extractFileName(
        response.headers['content-disposition'],
        `near-miss-${id}.pdf`
      ),
    };
  },

  async downloadNearMissEvidencePhoto(previewUrl: string): Promise<Blob> {
    const url = /^https?:\/\//i.test(previewUrl)
      ? previewUrl
      : `${API_BASE_URL}${previewUrl}`;
    const response = await apiClient.get<Blob>(url, { responseType: 'blob' });
    return response.data;
  },

  async exportAuditorBundle(
    request: SafetyAuditorBundleExportRequest
  ): Promise<SafetyDownloadResult> {
    const response = await apiClient.post<Blob>(
      buildSafetyApiUrl('/export/auditor-bundle/'),
      request,
      { responseType: 'blob' }
    );
    return {
      blob: response.data,
      fileName: extractFileName(
        response.headers['content-disposition'],
        'safety-auditor-bundle.zip'
      ),
    };
  },

  async getScmMeetings(filters: SafetyScmFilters = {}) {
    const response = await apiClient.get<
      SafetyScmMeeting[] | PaginatedResponse<SafetyScmMeeting>
    >(buildSafetyApiUrl('/scm/'), {
      params: buildParams(filters),
    });
    return unwrapPaginatedResults(response.data);
  },

  async getScmMeeting(id: number | string) {
    const response = await apiClient.get<SafetyScmMeeting>(
      buildSafetyApiUrl(`/scm/${id}/`)
    );
    return response.data;
  },

  async getScmCreateRegularConfig(vesselId?: string | null) {
    const response = await apiClient.get<SafetyScmFormConfig>(
      buildSafetyApiUrl('/scm/create-regular/'),
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async getScmCreateAdhocConfig(vesselId?: string | null) {
    const response = await apiClient.get<SafetyScmFormConfig>(
      buildSafetyApiUrl('/scm/create-adhoc/'),
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async createScmMeeting(payload: SafetyScmCreatePayload) {
    const response = await apiClient.post<SafetyScmMeeting>(
      buildSafetyApiUrl('/scm/'),
      payload
    );
    return response.data;
  },

  async updateScmMeeting(id: number | string, payload: SafetyScmCreatePayload) {
    const response = await apiClient.patch<SafetyScmMeeting>(
      buildSafetyApiUrl(`/scm/${id}/`),
      payload
    );
    return response.data;
  },

  async submitScmMeeting(id: number | string, payload: SafetyScmSubmitPayload) {
    const response = await apiClient.post<SafetyScmMeeting>(
      buildSafetyApiUrl(`/scm/${id}/submit/`),
      payload
    );
    return response.data;
  },

  async addScmOfficeReview(
    id: number | string,
    payload: SafetyScmOfficeReviewPayload
  ) {
    const response = await apiClient.post<SafetyScmMeeting>(
      buildSafetyApiUrl(`/scm/${id}/office-comment/`),
      payload
    );
    return response.data;
  },

  async getScmAgenda(
    id: number | string,
    options: { includeCarriedForward?: boolean } = {}
  ) {
    const suffix = options.includeCarriedForward
      ? '?include_carried_forward=1'
      : '';
    const response = await apiClient.get<SafetyScmAgendaPayload>(
      buildSafetyApiUrl(`/scm/${id}/agenda/${suffix}`)
    );
    return response.data;
  },

  async updateScmAgenda(
    id: number | string,
    payload: SafetyScmAgendaUpdatePayload
  ) {
    const response = await apiClient.patch<SafetyScmAgendaPayload>(
      buildSafetyApiUrl(`/scm/${id}/agenda/`),
      payload
    );
    return response.data;
  },

  async getScmClosedSinceLast(id: number | string) {
    const response = await apiClient.get<SafetyScmClosedSinceLastPayload>(
      buildSafetyApiUrl(`/scm/${id}/closed-since-last/`)
    );
    return response.data;
  },

  async getScmAutoFeed(id: number | string) {
    const response = await apiClient.get<SafetyScmAutoFeedPayload>(
      buildSafetyApiUrl(`/scm/${id}/auto-feed/`)
    );
    return response.data;
  },

  async getScmOpenFindings(vesselId?: string | null) {
    const response = await apiClient.get<SafetyScmAutoFeedPayload>(
      buildSafetyApiUrl('/soi/open-findings/'),
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async getScmAttendance(id: number | string) {
    const response = await apiClient.get<SafetyScmAttendancePayload>(
      buildSafetyApiUrl(`/scm/${id}/attendance/`)
    );
    return response.data;
  },

  async acknowledgeScmAttendance(id: number | string) {
    const response = await apiClient.post(
      buildSafetyApiUrl(`/scm/${id}/attendance/acknowledge/`),
      { acknowledged: true }
    );
    return response.data as {
      acknowledged: boolean;
      acknowledged_at?: string;
      acknowledged_by?: string;
    };
  },

  async downloadScmPdf(id: number | string): Promise<SafetyDownloadResult> {
    const response = await apiClient.get<Blob>(
      buildSafetyApiUrl(`/export/scm/${id}/pdf/`),
      { responseType: 'blob' }
    );
    return {
      blob: response.data,
      fileName: extractFileName(
        response.headers['content-disposition'],
        `scm-${id}.pdf`
      ),
    };
  },

  async getSoiCompliance(vesselId?: string | null) {
    const response = await apiClient.get<SafetySoiComplianceResponse>(
      buildSafetyApiUrl('/soi/compliance/'),
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async getSoiCreateConfig(
    options: {
      plannedDate?: string;
      safetyOfficerCrewId?: string;
      vesselId?: string;
    } = {}
  ) {
    const response = await apiClient.get<SafetySoiCreateConfigResponse>(
      buildSafetyApiUrl('/soi/create/'),
      {
        params: buildParams({
          planned_date: options.plannedDate,
          vessel_id: options.vesselId,
        }),
      }
    );
    return response.data;
  },

  async getSoiInspections(filters: SafetySoiFilters = {}) {
    const response = await apiClient.get<
      SafetySoiInspection[] | PaginatedResponse<SafetySoiInspection>
    >(buildSafetyApiUrl('/soi/'), {
      params: buildParams(filters),
    });
    return unwrapPaginatedResults(response.data);
  },

  async createSoiInspection(payload: SafetySoiCreatePayload) {
    const response = await apiClient.post<SafetySoiInspection>(
      buildSafetyApiUrl('/soi/'),
      payload
    );
    return response.data;
  },

  async getSoiOfficerSetting(vesselId?: string | null) {
    const response = await apiClient.get<SafetySoiOfficerSetting>(
      buildSafetyApiUrl('/soi/officer-setting/'),
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async updateSoiOfficerSetting(
    payload: SafetySoiOfficerSettingPayload,
    vesselId?: string | null
  ) {
    const response = await apiClient.patch<SafetySoiOfficerSetting>(
      buildSafetyApiUrl('/soi/officer-setting/'),
      payload,
      {
        params: buildParams({ vessel_id: vesselId }),
      }
    );
    return response.data;
  },

  async getSoiInspection(id: number | string) {
    const response = await apiClient.get<SafetySoiInspection>(
      buildSafetyApiUrl(`/soi/${id}/`)
    );
    return response.data;
  },

  async downloadSoiChecklist(id: number | string, format: 'PDF' | 'XLSX') {
    const response = await apiClient.get<Blob>(
      buildSafetyApiUrl(`/soi/${id}/checklist/download/`),
      {
        params: buildParams({ format }),
        responseType: 'blob',
      }
    );
    return {
      blob: response.data,
      fileName: extractFileName(
        response.headers['content-disposition'],
        `soi-${id}.${format === 'PDF' ? 'pdf' : 'xlsx'}`
      ),
    };
  },

  async downloadSoiSummaryPdf(
    id: number | string
  ): Promise<SafetyDownloadResult> {
    const response = await apiClient.get<Blob>(
      buildSafetyApiUrl(`/soi/${id}/pdf/`),
      { responseType: 'blob' }
    );
    return {
      blob: response.data,
      fileName: extractFileName(
        response.headers['content-disposition'],
        `soi-${id}-summary.pdf`
      ),
    };
  },

  async recoverSoiChecklist(
    id: number | string,
    payload: { format: 'PDF' | 'XLSX'; reason: string }
  ) {
    const response = await apiClient.post<Blob>(
      buildSafetyApiUrl(`/soi/${id}/lost-paper/recover/`),
      payload,
      {
        responseType: 'blob',
      }
    );
    return {
      blob: response.data,
      fileName: extractFileName(
        response.headers['content-disposition'],
        `soi-${id}-recovery.${payload.format === 'PDF' ? 'pdf' : 'xlsx'}`
      ),
    };
  },

  async getSoiPickAreas(id: number | string) {
    const response = await apiClient.get<SafetySoiPickAreasResponse>(
      buildSafetyApiUrl(`/soi/${id}/pick-areas/`)
    );
    return response.data;
  },

  async getSoiCloseSnapshot(id: number | string) {
    const response = await apiClient.get<SafetySoiCloseSnapshot>(
      buildSafetyApiUrl(`/soi/${id}/close/`)
    );
    return response.data;
  },

  async closeSoiInspection(
    id: number | string,
    payload: SafetySoiClosePayload
  ) {
    const response = await apiClient.post<SafetySoiCloseSnapshot>(
      buildSafetyApiUrl(`/soi/${id}/close/`),
      payload
    );
    return response.data;
  },

  async getSoiFindings(id: number | string) {
    const response = await apiClient.get<
      SafetySoiFinding[] | PaginatedResponse<SafetySoiFinding>
    >(buildSafetyApiUrl(`/soi/${id}/findings/`));
    return unwrapPaginatedResults(response.data);
  },

  async createSoiFinding(
    id: number | string,
    payload: SafetySoiFindingCreatePayload
  ) {
    const response = await apiClient.post<SafetySoiFindingCreateResponse>(
      buildSafetyApiUrl(`/soi/${id}/findings/`),
      payload
    );
    return response.data;
  },

  async uploadSoiFindingPhoto(id: number | string, file: File) {
    const formData = new FormData();
    formData.append('photo', file);
    const response = await apiClient.post<SafetySoiPhotoUploadResponse>(
      buildSafetyApiUrl(`/soi/${id}/findings/photo/`),
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  async submitSoiAreas(id: number | string, submittedAreaIds: number[]) {
    const response = await apiClient.post<SafetySoiFindingSubmitResponse>(
      buildSafetyApiUrl(`/soi/${id}/submit/`),
      { submitted_area_ids: submittedAreaIds }
    );
    return response.data;
  },

  async getSoiFinding(findingId: number | string) {
    const response = await apiClient.get<SafetySoiFinding>(
      buildSafetyApiUrl(`/soi/findings/${findingId}/`)
    );
    return response.data;
  },

  async markSoiFindingPendingClosure(
    findingId: number | string,
    payload: SafetySoiFindingPendingClosurePayload
  ) {
    const response = await apiClient.post<SafetySoiFindingActionResponse>(
      buildSafetyApiUrl(`/soi/findings/${findingId}/pending-closure/`),
      payload
    );
    return response.data;
  },

  async approveSoiFindingClosure(
    findingId: number | string,
    payload: SafetySoiFindingApprovalPayload
  ) {
    const response = await apiClient.post<SafetySoiFindingActionResponse>(
      buildSafetyApiUrl(`/soi/findings/${findingId}/approve-closure/`),
      payload
    );
    return response.data;
  },

  async reopenSoiFinding(
    findingId: number | string,
    payload: SafetySoiFindingReopenPayload
  ) {
    const response = await apiClient.post<SafetySoiFindingActionResponse>(
      buildSafetyApiUrl(`/soi/findings/${findingId}/reopen/`),
      payload
    );
    return response.data;
  },

  async getSoiApplicabilityRequestScreen(id: number | string) {
    const response = await apiClient.get<SafetySoiApplicabilityRequestScreen>(
      buildSafetyApiUrl(`/soi/${id}/applicability/request/`)
    );
    return response.data;
  },

  async submitSoiApplicabilityRequest(
    id: number | string,
    payload: SafetySoiApplicabilityRequestPayload
  ) {
    const response = await apiClient.post<SafetySoiApplicabilityRequestResult>(
      buildSafetyApiUrl(`/soi/${id}/applicability/request/`),
      payload
    );
    return response.data;
  },

  async getSoiApplicabilityApprovalScreen(id: number | string) {
    const response = await apiClient.get<SafetySoiApplicabilityApprovalScreen>(
      buildSafetyApiUrl(`/soi/${id}/applicability/approve/`)
    );
    return response.data;
  },

  async submitSoiApplicabilityApproval(
    id: number | string,
    payload: SafetySoiApplicabilityApprovalPayload
  ) {
    const response = await apiClient.post<SafetySoiApplicabilityApprovalResult>(
      buildSafetyApiUrl(`/soi/${id}/applicability/approve/`),
      payload
    );
    return response.data;
  },

  async searchRecords(
    query: string,
    options: { includeArchived?: boolean; recordType?: string } = {}
  ) {
    const response = await apiClient.get<SafetySearchResponse>(
      buildSafetyApiUrl('/search/'),
      {
        params: buildParams({
          q: query,
          include_archived: options.includeArchived,
          record_type:
            options.recordType && options.recordType !== 'ALL'
              ? options.recordType
              : undefined,
        }),
      }
    );
    return response.data;
  },
};
