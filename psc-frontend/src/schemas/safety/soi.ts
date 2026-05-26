import { z } from "zod";

export const SAFETY_SOI_SCHEMA_VERSION = 1 as const;
export const SAFETY_SOI_MAX_SELECTED_AREAS = 4 as const;

export const safetySoiAreaOptionSchema = z.object({
  applicable: z.boolean(),
  area_id: z.number().int().min(1),
  area_name: z.string(),
  due_at: z.string().nullable(),
  last_inspected_at: z.string().nullable(),
  map_id: z.number().int().nullable(),
  schema_version: z.number().int().min(1),
  section_12_flag: z.boolean(),
});

export const safetySoiCrewSnapshotSchema = z.object({
  crew_id: z.string().min(1),
  department: z.string().min(1),
  rank: z.string().min(1),
  vessel_id: z.string().min(1),
});

export const safetySoiChecklistVersionSchema = z.object({
  active: z.boolean(),
  effective_from: z.string().min(1),
  effective_to: z.string().nullable(),
  id: z.number().int().min(1),
  source_description: z.string().min(1),
  version_label: z.string().min(1),
});

export const safetySoiSection12StatusSchema = z.object({
  covered_by_inspection_id: z.number().int().nullable(),
  covered_by_inspection_reference: z.string().nullable(),
  covered_planned_date: z.string().nullable(),
  covered_this_cycle: z.boolean(),
  cycle_end: z.string().min(1),
  cycle_label: z.string().min(1),
  cycle_start: z.string().min(1),
  next_allowed_date: z.string().nullable(),
  prompt_required: z.boolean(),
  vessel_id: z.string().min(1),
});

export const safetySoiCreateSchema = z.object({
  area_ids: z.array(z.number().int().min(1)).min(1).max(SAFETY_SOI_MAX_SELECTED_AREAS),
  assistant_crew_id: z.string().min(1),
  cycle_label: z.string().min(1),
  inspection_reference: z.string().min(1),
  planned_date: z.string().min(1),
  safety_officer_crew_id: z.string().min(1),
  schema_version: z.literal(SAFETY_SOI_SCHEMA_VERSION),
  section_12_included: z.boolean(),
  trainee_crew_ids: z.array(z.string().min(1)).max(3),
  vessel_id: z.string().min(1),
});

export type SafetySoiAreaOption = z.infer<typeof safetySoiAreaOptionSchema>;
export type SafetySoiChecklistVersion = z.infer<typeof safetySoiChecklistVersionSchema>;
export type SafetySoiCreateValues = z.infer<typeof safetySoiCreateSchema>;
export type SafetySoiCrewSnapshot = z.infer<typeof safetySoiCrewSnapshotSchema>;
export type SafetySoiSection12Status = z.infer<typeof safetySoiSection12StatusSchema>;

export interface SafetySoiCreateConfig {
  areas: SafetySoiAreaOption[];
  assistant_candidates: SafetySoiCrewSnapshot[];
  checklist_version: SafetySoiChecklistVersion;
  max_trainees: number;
  section_12_status: SafetySoiSection12Status;
  safety_officer: SafetySoiCrewSnapshot;
  trainee_candidates: SafetySoiCrewSnapshot[];
}

export interface SafetySoiApplicabilityRequestDraft {
  area_id: number;
  master_signature: string;
  new_applicable: boolean;
  reason: string;
}

export interface SafetySoiApplicabilityPendingRequest {
  area_id: number;
  area_name: string;
  master_requested_at: string;
  master_requested_by: string;
  new_applicable: boolean;
  old_applicable: boolean;
  reason: string;
  request_id: number;
  section_12_flag: boolean;
  vessel_id: string;
}

export interface SafetySoiApplicabilityApprovalDraft {
  area_id: number;
  dpa_decision: "APPROVED" | "REJECTED";
  dpa_signature: string;
  reason: string;
}

export interface SafetySoiComplianceArea {
  area_id: number;
  area_name: string;
  days_overdue: number | null;
  days_since_last_inspection: number | null;
  days_until_due: number | null;
  due_at: string | null;
  last_inspected_at: string | null;
  status: "GREEN" | "AMBER" | "RED" | "NA" | "PENDING";
}

export interface SafetySoiComplianceSummary {
  amber_area_count: number;
  applicable_area_count: number;
  areas: SafetySoiComplianceArea[];
  compliance_percent: number | null;
  display_value: string;
  inspected_area_count: number;
  label: string;
  overdue_area_count: number;
  status: "GREEN" | "AMBER" | "RED" | "NA";
}

export interface SafetySoiDigitalSignatureSnapshot {
  device_fingerprint_last8: string;
  signed_at: string;
  signer_display_name: string;
}

export interface SafetySoiCrewRotationCrew {
  crew_id: string;
  inspections_accompanied: number;
}

export interface SafetySoiCrewRotationSummary {
  accompanied_crew_count: number;
  coverage_percent: number | null;
  crew: SafetySoiCrewRotationCrew[];
  display_value: string;
  total_active_crew: number;
  vessel_id: string;
  window_days: number;
  window_end: string;
  window_start: string;
}

export interface SafetySoiFindingSummary {
  carried_forward_count: number;
  closed_count: number;
  master_approved_count: number;
  open_count: number;
  pending_closure_count: number;
  total_count: number;
}

export interface SafetySoiDownloadArea {
  area_id: number;
  area_name: string;
  section_12_flag: boolean;
}

export interface SafetySoiDownloadSnapshot {
  checklist_format: "PDF" | "XLSX" | null;
  checklist_unique_id: string | null;
  cycle_label: string;
  id: number;
  inspection_reference: string;
  lost_paper_flag: boolean;
  lost_paper_note: string | null;
  planned_date: string;
  selected_areas: SafetySoiDownloadArea[];
  state: "PLANNED" | "DOWNLOADED" | "IN_FIELDWORK" | "REPORTED" | "CLOSED";
}

export interface SafetySoiRegisterItem {
  assistant_crew_id: string;
  id: number;
  inspection_reference: string;
  planned_date: string;
  selected_area_count: number;
  state: string;
  trainee_count: number;
}

export interface SafetySoiCloseSnapshot {
  checklist_unique_id: string | null;
  closed_at: string | null;
  crew_rotation: SafetySoiCrewRotationSummary;
  finding_summary: SafetySoiFindingSummary;
  inspection_id: number;
  inspection_reference: string;
  planned_date: string;
  selected_areas: Array<{
    area_id: number;
    area_name: string;
    display_order: number;
    inspected: boolean;
    inspection_id: number;
    last_inspected_at: string | null;
    notes: string | null;
    schema_version: number;
    section_12_flag: boolean;
    selection_id: number;
  }>;
  signature: SafetySoiDigitalSignatureSnapshot | null;
  state: "PLANNED" | "DOWNLOADED" | "IN_FIELDWORK" | "REPORTED" | "CLOSED";
  trainees: Array<{
    crew_id: string;
    inspection_id: number;
    schema_version: number;
    trainee_slot: number;
  }>;
  vessel_id: string;
}

export const safetySoiDemoConfig: SafetySoiCreateConfig = {
  areas: [
    {
      applicable: true,
      area_id: 3,
      area_name: "Navigating Bridge & Monkey Island",
      due_at: "2026-05-01T00:00:00Z",
      last_inspected_at: "2026-02-14T10:00:00Z",
      map_id: 301,
      schema_version: 1,
      section_12_flag: false,
    },
    {
      applicable: true,
      area_id: 5,
      area_name: "Mooring Deck + Forward Station",
      due_at: "2026-05-01T00:00:00Z",
      last_inspected_at: "2026-02-11T08:30:00Z",
      map_id: 305,
      schema_version: 1,
      section_12_flag: false,
    },
    {
      applicable: true,
      area_id: 8,
      area_name: "Engine Control Room + Machinery Flat",
      due_at: "2026-05-01T00:00:00Z",
      last_inspected_at: "2026-02-09T12:00:00Z",
      map_id: 308,
      schema_version: 1,
      section_12_flag: false,
    },
    {
      applicable: true,
      area_id: 13,
      area_name: "Cross-cutting Safety & Culture",
      due_at: "2026-05-01T00:00:00Z",
      last_inspected_at: null,
      map_id: 313,
      schema_version: 1,
      section_12_flag: true,
    },
  ],
  assistant_candidates: [
    {
      crew_id: "2e-7",
      department: "ENGINE",
      rank: "2/E",
      vessel_id: "7",
    },
    {
      crew_id: "3e-7",
      department: "ENGINE",
      rank: "3/E",
      vessel_id: "7",
    },
  ],
  trainee_candidates: [
    {
      crew_id: "cadet-7",
      department: "DECK",
      rank: "CADET",
      vessel_id: "7",
    },
    {
      crew_id: "2e-7",
      department: "ENGINE",
      rank: "2/E",
      vessel_id: "7",
    },
  ],
  checklist_version: {
    active: true,
    effective_from: "2026-04-17",
    effective_to: null,
    id: 1,
    source_description: "SQE S 608 baseline - SSQE Rev 02 + Section 12",
    version_label: "v1.0",
  },
  max_trainees: 3,
  section_12_status: {
    covered_by_inspection_id: null,
    covered_by_inspection_reference: null,
    covered_planned_date: null,
    covered_this_cycle: false,
    cycle_end: "2026-06-30",
    cycle_label: "Q2/2026",
    cycle_start: "2026-04-01",
    next_allowed_date: null,
    prompt_required: true,
    vessel_id: "7",
  },
  safety_officer: {
    crew_id: "co-7",
    department: "DECK",
    rank: "CO",
    vessel_id: "7",
  },
};

export const safetySoiDemoCompliance: SafetySoiComplianceSummary = {
  amber_area_count: 1,
  applicable_area_count: 4,
  areas: [
    {
      area_id: 3,
      area_name: "Navigating Bridge & Monkey Island",
      days_overdue: null,
      days_since_last_inspection: 82,
      days_until_due: 8,
      due_at: "2026-05-09T10:00:00Z",
      last_inspected_at: "2026-02-16T10:00:00Z",
      status: "AMBER",
    },
    {
      area_id: 5,
      area_name: "Mooring Deck + Forward Station",
      days_overdue: null,
      days_since_last_inspection: 54,
      days_until_due: 36,
      due_at: "2026-06-06T08:30:00Z",
      last_inspected_at: "2026-03-08T08:30:00Z",
      status: "GREEN",
    },
    {
      area_id: 8,
      area_name: "Engine Control Room + Machinery Flat",
      days_overdue: null,
      days_since_last_inspection: 48,
      days_until_due: 42,
      due_at: "2026-06-12T12:00:00Z",
      last_inspected_at: "2026-03-14T12:00:00Z",
      status: "GREEN",
    },
    {
      area_id: 13,
      area_name: "Cross-cutting Safety & Culture",
      days_overdue: null,
      days_since_last_inspection: null,
      days_until_due: null,
      due_at: null,
      last_inspected_at: null,
      status: "PENDING",
    },
  ],
  compliance_percent: 75,
  display_value: "75%",
  inspected_area_count: 3,
  label: "SOI Compliance %",
  overdue_area_count: 0,
  status: "AMBER",
};

export const safetySoiDemoDraft: SafetySoiCreateValues = {
  area_ids: [3, 8, 13],
  assistant_crew_id: "2e-7",
  cycle_label: "Q2/2026",
  inspection_reference: "SOI/ABC/26/07",
  planned_date: "2026-05-01",
  safety_officer_crew_id: "co-7",
  schema_version: SAFETY_SOI_SCHEMA_VERSION,
  section_12_included: true,
  trainee_crew_ids: ["cadet-17", "oiler-2"],
  vessel_id: "7",
};

export const safetySoiDemoPickAreaStatus: SafetySoiSection12Status = {
  covered_by_inspection_id: 42,
  covered_by_inspection_reference: safetySoiDemoDraft.inspection_reference,
  covered_planned_date: safetySoiDemoDraft.planned_date,
  covered_this_cycle: true,
  cycle_end: "2026-06-30",
  cycle_label: "Q2/2026",
  cycle_start: "2026-04-01",
  next_allowed_date: "2026-07-01",
  prompt_required: false,
  vessel_id: safetySoiDemoDraft.vessel_id,
};

export const safetySoiDemoApplicabilityRequest: SafetySoiApplicabilityRequestDraft = {
  area_id: 5,
  master_signature: "Captain Rao|bridge-ipad-7",
  new_applicable: false,
  reason:
    "This vessel variant does not carry the forward mooring deck arrangement represented in Area 5. " +
    "The layout is permanently absent in the approved GA plan, class records, and onboard SMS references, " +
    "so repeated selection would distort the 90-day SOI compliance surface for this ship.",
};

export const safetySoiDemoPendingApplicabilityRequests: SafetySoiApplicabilityPendingRequest[] = [
  {
    area_id: 5,
    area_name: "Mooring Deck + Forward Station",
    master_requested_at: "2026-04-28T09:15:00Z",
    master_requested_by: "master-7",
    new_applicable: false,
    old_applicable: true,
    reason: safetySoiDemoApplicabilityRequest.reason,
    request_id: 701,
    section_12_flag: false,
    vessel_id: "7",
  },
];

export const safetySoiDemoApplicabilityApproval: SafetySoiApplicabilityApprovalDraft = {
  area_id: 5,
  dpa_decision: "APPROVED",
  dpa_signature: "DPA Menon|office-lt-4",
  reason:
    "Approved after reviewing the vessel GA plan and class attachment. Keep the area excluded until fleet " +
    "operations or the vessel arrangement changes.",
};

export const safetySoiDemoDownload: SafetySoiDownloadSnapshot = {
  checklist_format: null,
  checklist_unique_id: null,
  cycle_label: safetySoiDemoDraft.cycle_label,
  id: 42,
  inspection_reference: safetySoiDemoDraft.inspection_reference,
  lost_paper_flag: false,
  lost_paper_note: null,
  planned_date: safetySoiDemoDraft.planned_date,
  selected_areas: safetySoiDemoConfig.areas
    .filter((area) => safetySoiDemoDraft.area_ids.includes(area.area_id))
    .map((area) => ({
      area_id: area.area_id,
      area_name: area.area_name,
      section_12_flag: area.section_12_flag,
    })),
  state: "PLANNED",
};

export const safetySoiDemoCloseSnapshot: SafetySoiCloseSnapshot = {
  checklist_unique_id: "SOI-0000007-20260505-0014",
  closed_at: null,
  crew_rotation: {
    accompanied_crew_count: 2,
    coverage_percent: 50,
    crew: [
      {
        crew_id: "cadet-17",
        inspections_accompanied: 2,
      },
      {
        crew_id: "oiler-2",
        inspections_accompanied: 1,
      },
    ],
    display_value: "50%",
    total_active_crew: 4,
    vessel_id: "7",
    window_days: 365,
    window_end: "2026-05-06T09:30:00Z",
    window_start: "2025-05-06T09:30:00Z",
  },
  finding_summary: {
    carried_forward_count: 0,
    closed_count: 1,
    master_approved_count: 0,
    open_count: 1,
    pending_closure_count: 1,
    total_count: 2,
  },
  inspection_id: 42,
  inspection_reference: "SOI/ABC/26/14",
  planned_date: "2026-05-05",
  selected_areas: [
    {
      area_id: 3,
      area_name: "Navigating Bridge & Monkey Island",
      display_order: 3,
      inspected: true,
      inspection_id: 42,
      last_inspected_at: "2026-05-05T07:30:00Z",
      notes: null,
      schema_version: 1,
      section_12_flag: false,
      selection_id: 4203,
    },
    {
      area_id: 8,
      area_name: "Engine Control Room + Machinery Flat",
      display_order: 8,
      inspected: true,
      inspection_id: 42,
      last_inspected_at: "2026-05-05T07:30:00Z",
      notes: null,
      schema_version: 1,
      section_12_flag: false,
      selection_id: 4208,
    },
    {
      area_id: 13,
      area_name: "Cross-cutting Safety & Culture",
      display_order: 13,
      inspected: true,
      inspection_id: 42,
      last_inspected_at: "2026-05-05T07:30:00Z",
      notes: "Quarterly Section 12 carried on this event.",
      schema_version: 1,
      section_12_flag: true,
      selection_id: 4213,
    },
  ],
  signature: null,
  state: "REPORTED",
  trainees: [
    {
      crew_id: "cadet-17",
      inspection_id: 42,
      schema_version: 1,
      trainee_slot: 1,
    },
    {
      crew_id: "oiler-2",
      inspection_id: 42,
      schema_version: 1,
      trainee_slot: 2,
    },
  ],
  vessel_id: "7",
};

export const safetySoiDemoCrewPool: SafetySoiCrewSnapshot[] = [
  safetySoiDemoConfig.safety_officer,
  ...safetySoiDemoConfig.assistant_candidates,
  {
    crew_id: "cadet-17",
    department: "DECK",
    rank: "CADET",
    vessel_id: "7",
  },
  {
    crew_id: "oiler-2",
    department: "ENGINE",
    rank: "OILER",
    vessel_id: "7",
  },
  {
    crew_id: "deck-cadet-4",
    department: "DECK",
    rank: "DECK CADET",
    vessel_id: "7",
  },
];

export const safetySoiDemoRegister: SafetySoiRegisterItem[] = [
  {
    assistant_crew_id: "2e-7",
    id: 42,
    inspection_reference: "SOI/ABC/26/06",
    planned_date: "2026-04-18",
    selected_area_count: 4,
    state: "PLANNED",
    trainee_count: 1,
  },
  {
    assistant_crew_id: "3e-7",
    id: 37,
    inspection_reference: "SOI/ABC/26/05",
    planned_date: "2026-03-21",
    selected_area_count: 3,
    state: "DOWNLOADED",
    trainee_count: 0,
  },
];
