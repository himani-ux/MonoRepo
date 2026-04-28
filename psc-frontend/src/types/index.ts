/**
 * Central type definitions for the VIMS Inspection application
 *
 * This file exports all shared types used across the application.
 * Feature-specific types may be co-located with their features.
 */

import {
  INSPECTION_TYPES,
  PSC_SUBTYPES,
  INSPECTION_STATUS,
  OPERATIONAL_STATUS,
  CAR_STATUS,
  WORKFLOW_ACTIONS,
  EVIDENCE_TYPES,
  ACTION_TYPES,
  USER_ROLES,
  SYNC_STATUS,
} from '@/lib/utils/constants';

// ============================================================================
// Utility Types
// ============================================================================

/** Extract values from a const object */
export type ValueOf<T> = T[keyof T];

/** Make specific properties optional */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/** Make specific properties required */
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>;

// ============================================================================
// Enum Types (derived from constants)
// ============================================================================

export type InspectionType = ValueOf<typeof INSPECTION_TYPES>;
export type PSCSubtype = ValueOf<typeof PSC_SUBTYPES>;
export type InspectionStatus = ValueOf<typeof INSPECTION_STATUS>;
export type OperationalStatus = ValueOf<typeof OPERATIONAL_STATUS>;
export type CARStatus = ValueOf<typeof CAR_STATUS>;
export type WorkflowAction = ValueOf<typeof WORKFLOW_ACTIONS>;
export type EvidenceType = ValueOf<typeof EVIDENCE_TYPES>;
export type ActionType = ValueOf<typeof ACTION_TYPES>;
export type UserRole = ValueOf<typeof USER_ROLES>;
export type SyncStatus = ValueOf<typeof SYNC_STATUS>;

// ============================================================================
// User & Authentication
// ============================================================================

/** User type from JWT token claims */
export type UserType = 'vessel' | 'office';

/** User information from authentication */
export interface User {
  id: string;
  user_type: UserType;
  full_name: string;
  role: string;
  vessel_id: string | null;
  vessel_code: string | null;
  email: string | null;
  employee_id: string | null;
  crew_id: string | null;
  form_ids?: string[];
  process_ids?: string[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// ============================================================================
// Inspection
// ============================================================================

export interface Inspection {
  id: number;
  vessel_id: number;
  vessel_name: string;
  inspection_type: InspectionType;
  psc_subtype: PSCSubtype | null;
  inspection_date: string;
  port: string;
  port_state: string;
  mou_code: string | null;
  inspector_name: string | null;
  is_detention: boolean;
  detention_reason: string | null;
  def_reported: 'YES' | 'NO' | null;
  status: InspectionStatus;
  operational_status: OperationalStatus;
  open_deficiency_count: number;
  closed_deficiency_count: number;
  report_file: string | null;
  deficiency_count: number;
  created_by: number;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  pic_reviewed_at: string | null;
  dpa_closed_at: string | null;
}

export interface InspectionListItem
  extends Pick<
    Inspection,
    | 'id'
    | 'vessel_name'
    | 'inspection_type'
    | 'inspection_date'
    | 'port'
    | 'is_detention'
    | 'status'
    | 'deficiency_count'
  > {}

export interface CreateInspectionInput {
  vessel_id: string;
  inspection_type: InspectionType;
  psc_subtype?: PSCSubtype | null;
  inspection_date: string;
  port_place: string;
  country?: string;
  mou_id?: string | null;
  authority?: string | null;
  inspector_name?: string | null;
  is_detention: boolean;
  detention_reason?: string | null;
  def_reported: 'YES' | 'NO';
}

export interface UpdateInspectionInput extends Partial<CreateInspectionInput> {}

/** Inspection report file attached to an inspection */
export interface InspectionReport {
  id: number;
  file_name: string;
  file_path: string;
  file_url?: string;
  file_size: number;
  mime_type: string;
  description: string | null;
  report_type: 'ORIGINAL' | 'FOLLOW_UP';
  uploaded_by: number;
  uploaded_by_name: string;
  uploaded_at: string;
}

/** Full inspection detail with nested deficiencies, reports, and activity */
export interface InspectionDetail extends Inspection {
  /** Vessel IMO number */
  imo_number: string | null;
  /** Authority that conducted the inspection */
  authority: string | null;
  /** Report reference number */
  report_reference: string | null;
  /** PIC review comments */
  pic_review_comments: string | null;
  /** DPA close comments */
  dpa_close_comments: string | null;
  /** Parent inspection ID for follow-ups */
  parent_inspection_id: number | null;
  /** Deficiencies with embedded CAR info */
  deficiencies: DeficiencyDetail[];
  /** Attached inspection reports */
  reports: InspectionReport[];
  /** Activity history events */
  activity_history: ActivityEvent[];
  /** Audit log entries (office only) */
  audit_log?: AuditLogEntry[];
}

// ============================================================================
// Deficiency
// ============================================================================

/** Deficiency vessel-side workflow status */
export type DefStatus =
  | 'ALLOCATED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'SUBMITTED';

export interface Deficiency {
  id: number;
  inspection_id: number;
  def_code: string;
  def_code_description: string;
  description: string;
  action_code: string | null;
  action_code_description: string | null;
  car_id: number;
  car_status: CARStatus;
  created_at: string;
  updated_at: string;
}

/** Embedded CAR summary in deficiency detail */
export interface DeficiencyCARSummary {
  id: number;
  car_number: string;
  status: CARStatus;
}

/** Deficiency with embedded CAR object for inspection detail view */
export interface DeficiencyDetail {
  id: number;
  def_code: string;
  def_code_description: string;
  description: string;
  action_code: string | null;
  action_code_description: string | null;
  target_date: string | null;
  is_cleared: boolean;
  assigned_crew_id: string | null;
  assigned_crew_name: string | null;
  def_status: DefStatus;
  reviewer_crew_id: string | null;
  owner_rank: string | null;
  owner_name: string | null;
  reviewer_rank: string | null;
  reviewer_name: string | null;
  car: DeficiencyCARSummary;
  workflow_history?: WorkflowHistoryEvent[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowHistoryEvent {
  event_type: string;
  event_description: string;
  performed_by_name: string | null;
  performed_at: string;
}

export interface CreateDeficiencyInput {
  def_code: string;
  def_text: string;
  action_code: string;
  target_date?: string;
  assigned_crew_id?: string;
}

// ============================================================================
// CAR (Corrective Action Report)
// ============================================================================

export interface CAR {
  id: number;
  car_number: string;
  deficiency_id: number;
  def_code: string;
  def_code_description: string;
  deficiency_description: string;
  inspection_id: number;
  inspection_type: InspectionType;
  inspection_date: string;
  vessel_id: number;
  vessel_name: string;
  status: CARStatus;
  root_cause_summary: string | null;
  clc_codes: string[];
  target_date: string | null;
  completion_date: string | null;
  evidence: Evidence[];
  corrective_actions: CorrectiveAction[];
  activity_events: ActivityEvent[];
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  pic_accepted_at: string | null;
  dpa_closed_at: string | null;
}

/** List item matching CARListSerializer backend response */
export interface CARListItem {
  id: number;
  car_number: string;
  status: CARStatus;
  status_display: string;
  root_cause_summary: string | null;
  target_date: string | null;
  pv_due: boolean;
  rework_count: number;
  created_date: string;
  // Deficiency info (denormalized)
  def_code: string;
  deficiency_description: string;
  deficiency_is_cleared: boolean;
  // Inspection info
  inspection_id: number;
  inspection_type: string;
  inspection_date: string;
  vessel_id: number;
  vessel_name: string;
  vessel_code: string;
  // Counts
  action_count: number;
  completed_action_count: number;
  before_evidence_count: number;
  after_evidence_count: number;
}

export interface UpdateCARInput {
  root_cause_summary?: string;
  target_date?: string | null;
  clc_item_ids?: string[];
  custom_cause_text?: string;
}

// ---- CAR Detail nested types (matching backend serializers) ----

/** Deficiency info nested in CAR detail (from DeficiencyNestedSerializer) */
export interface CARDetailDeficiency {
  id: string;
  def_code: string;
  def_code_id: string;
  description: string;
  action_code: string | null;
  action_code_id: number | null;
  target_date: string | null;
  is_cleared: boolean;
  cleared_date: string | null;
}

/** Inspection info nested in CAR detail (from InspectionNestedSerializer) */
export interface CARDetailInspection {
  id: string;
  inspection_type: string;
  psc_subtype: string | null;
  inspection_date: string;
  port_place: string;
  vessel_id: string;
  vessel_name: string;
}

/** CLC code mapping for CAR (from CarClcMappingSerializer) */
export interface CarClcMapping {
  id: number;
  clc_item_id: string;
  custom_cause_text: string;
}

/** Available workflow action from backend */
export interface AvailableAction {
  action: string;
  label: string;
  comment_required: boolean;
  role?: string;
}

/** Full CAR detail matching CARDetailSerializer backend response */
export interface CARDetail {
  id: number;
  car_number: string;
  status: CARStatus;
  status_display: string;
  root_cause_summary: string | null;
  target_date: string | null;
  // Verification
  verification_pending: boolean;
  // PIC Review
  pic_comment: string | null;
  pic_accepted_by: string | null;
  pic_accepted_at: string | null;
  // Rework
  rework_reason: string | null;
  rework_requested_by: string | null;
  rework_requested_at: string | null;
  rework_count: number;
  // DPA Close
  dpa_comment: string | null;
  dpa_closed_by: string | null;
  dpa_closed_at: string | null;
  // Last action
  last_action: string | null;
  last_action_by: string | null;
  last_action_at: string | null;
  last_action_comment: string | null;
  // Audit
  created_by: string;
  created_date: string;
  updated_by: string | null;
  updated_date: string | null;
  // Nested
  deficiency: CARDetailDeficiency | null;
  inspection: CARDetailInspection | null;
  clc_items: CarClcMapping[];
  corrective_actions: CorrectiveAction[];
  evidence: Evidence[];
  physical_verification: PhysicalVerification | null;
  activity_history: ActivityEvent[];
  audit_log: AuditLogEntry[];
  available_actions: AvailableAction[];
}

// ============================================================================
// Evidence
// ============================================================================

export interface Evidence {
  id: number;
  car_id: number;
  evidence_type: EvidenceType;
  evidence_type_display: string;
  file_name: string;
  file_path: string;
  preview_url?: string | null;
  file_size: number;
  mime_type: string;
  description: string;
  uploaded_by: string;
  uploaded_at: string;
}

export interface CreateEvidenceInput {
  evidence_type: EvidenceType;
  description: string;
  file: File;
}

// ============================================================================
// Corrective Action
// ============================================================================

export interface CrewMember {
  id: string;
  crew_id: string;
  first_name: string;
  surname: string;
  rank_name: string;
  department_name: string;
  display_name: string;
}

export interface CorrectiveAction {
  id: number;
  car_id: number;
  action_type: ActionType;
  action_type_display: string;
  description: string;
  owner_crew_id: string | null;
  owner_user_id: string | null;
  owner_name: string | null;
  due_date: string | null;
  is_completed: boolean;
  completed_at: string | null;
  completion_remarks: string | null;
  sequence_no: number;
  created_by: string;
  created_date: string;
}

export interface CreateCorrectiveActionInput {
  action_type: ActionType;
  description: string;
  owner_crew_id?: string | null;
  owner_user_id?: string | null;
  due_date?: string | null;
  client_id?: string;
}

export interface UpdateCorrectiveActionInput {
  description?: string;
  owner_crew_id?: string | null;
  owner_user_id?: string | null;
  due_date?: string | null;
}

// ============================================================================
// Activity & Audit
// ============================================================================

export interface ActivityEvent {
  id: number;
  entity_type: 'INSPECTION' | 'CAR';
  entity_id: number;
  event_type: string;
  event_description: string;
  performed_by: string;
  performed_by_name: string;
  performed_at: string;
  metadata: Record<string, unknown>;
}

export interface AuditLogEntry {
  id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  performed_by: string;
  performed_by_role: string;
  performed_at: string;
  is_office_edit_assist: boolean;
}

// ============================================================================
// Notification
// ============================================================================

/** Notification types matching backend NotificationType choices */
export type NotificationType =
  | 'CAR_CREATED'
  | 'CAR_SUBMITTED'
  | 'CAR_PIC_ACCEPTED'
  | 'CAR_REWORK_REQUESTED'
  | 'CAR_DPA_CLOSED'
  | 'ACTION_OVERDUE_WARNING'
  | 'ACTION_OVERDUE'
  | 'PSC_FOLLOW_UP_RECORDED'
  | 'CONFLICT_DETECTED'
  | 'CONFLICT_RESOLVED'
  | 'PHYSICAL_VERIFICATION_CREATED'
  | 'DEF_ASSIGNED'
  | 'CIRCULAR_CREATED'
  | 'CIRCULAR_PENDING_APPROVAL'
  | 'CIRCULAR_APPROVED'
  | 'CIRCULAR_REJECTED';

/** Notification matching backend NotificationListSerializer (12 fields) */
export interface Notification {
  id: string;
  recipient_type: 'CREW' | 'OFFICE';
  recipient_id: string;
  vessel_id: string | null;
  notification_type: NotificationType;
  title: string;
  message: string;
  entity_type: string | null;
  entity_id: string | null;
  is_read: boolean;
  read_at: string | null;
  created_date: string;
}

// ============================================================================
// Sync
// ============================================================================

export interface SyncQueueItem {
  id: string;
  entity_type: 'INSPECTION' | 'CAR' | 'DEFICIENCY' | 'EVIDENCE';
  entity_id: number | string;
  operation: 'CREATE' | 'UPDATE' | 'DELETE';
  data: Record<string, unknown>;
  status: SyncStatus;
  attempts: number;
  last_attempt_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface SyncConflict {
  id: string;
  vessel_id: number;
  entity_type: 'INSPECTION' | 'CAR';
  entity_id: string;
  server_data: Record<string, unknown>;
  vessel_data: Record<string, unknown>;
  conflicting_fields: string[];
  status: string;
  resolution: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  created_date: string;
}

// ============================================================================
// Master Data
// ============================================================================

/** MOU (Memorandum of Understanding) region code */
export interface MOUCode {
  mou_code: string;
  mou_name: string;
  region: string;
  sort_order: number;
}

/** PSC Action Code - what action was taken on a deficiency */
export interface PSCActionCode {
  action_code: number;
  definition: string;
  description: string;
  is_detention: boolean;
  requires_follow_up: boolean;
}

/** PIC (Person In Charge) code */
export interface PICCode {
  pic_code: string;
  pic_name: string;
  department: string;
  sort_order: number;
}

/** PSC Deficiency Category */
export interface PSCDefCategory {
  category_code: string;
  category_name: string;
  sort_order: number;
}

/** PSC Deficiency Code - deficiency classification */
export interface PSCDefCode {
  def_code: string;
  def_name: string;
  category_code: string;
  category_name: string;
  subcategory_code: string | null;
  subcategory_name: string | null;
  display_text: string;
  sort_order: number;
}

/** CLC (Comprehensive List of Causes) Category */
export interface CLCCategory {
  category_id: number;
  category_code: string;
  category_name: string;
  category_type: 'IMMEDIATE' | 'ROOT';
  parent_id: number | null;
  sort_order: number;
}

/** CLC Item - root cause classification */
export interface CLCItem {
  clc_code: string;
  item_name: string;
  item_description: string | null;
  category_id: number;
  category_code: string;
  category_name: string;
  category_type: 'IMMEDIATE' | 'ROOT';
  display_text: string;
  sort_order: number;
}

/** CLC Hierarchy leaf category from API: { name: string, items: { code: name } } */
export interface CLCHierarchyCategory {
  name: string;
  items: Record<string, string>;
}

/** Full CLC Hierarchy response matching backend CLCHierarchyView */
export interface CLCHierarchy {
  immediate_causes: {
    actions: Record<string, CLCHierarchyCategory>;
    conditions: Record<string, CLCHierarchyCategory>;
  };
  root_causes: {
    personal_factors: Record<string, CLCHierarchyCategory>;
    job_factors: Record<string, CLCHierarchyCategory>;
  };
}

// ============================================================================
// Physical Verification
// ============================================================================

export interface PhysicalVerification {
  id: number;
  car_id: number;
  status: string;
  status_display: string;
  scheduled_date: string | null;
  visit_date: string | null;
  visit_port: string | null;
  verifier_user_id: string | null;
  verifier_crew_id: string | null;
  comments: string | null;
  created_by: string;
  created_date: string;
  closed_by: string | null;
  closed_at: string | null;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
  };
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, string[]>;
}

// ============================================================================
// Filter Types
// ============================================================================

export interface InspectionFilters {
  vessel_id?: number;
  inspection_type?: InspectionType;
  status?: InspectionStatus;
  is_detention?: boolean;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface CARFilters {
  vessel_id?: number | string;
  status?: CARStatus;
  pv_due?: boolean;
  is_overdue?: boolean;
  has_missing_evidence?: boolean;
  date_from?: string;
  date_to?: string;
  search?: string;
}
