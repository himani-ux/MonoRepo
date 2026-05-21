import { z } from "zod";

export const SAFETY_SCM_SCHEMA_VERSION = 1 as const;

export const safetyScmSectionTemplate = [
  { agenda_item_number: 1, section_label: "Structured Review" },
  { agenda_item_number: 2, section_label: "Reserved" },
  { agenda_item_number: 3, section_label: "Safety Practice" },
  { agenda_item_number: 4, section_label: "Security" },
  { agenda_item_number: 5, section_label: "Environment" },
  { agenda_item_number: 6, section_label: "Health" },
  { agenda_item_number: 7, section_label: "Crew Welfare" },
  { agenda_item_number: 8, section_label: "Findings & Corrective Measures" },
  { agenda_item_number: 9, section_label: "Minutes of Meeting" },
  { agenda_item_number: 10, section_label: "Office Review" },
] as const;

export const safetyScmLegacyFieldTemplate = {
  1: [
    { field_key: "previous_minutes_reviewed", field_label: "Minutes previous safety committee reviewed", field_type: "BOOLEAN", required: true },
    { field_key: "absent_from_previous_meeting", field_label: "Absent date from previous meeting", field_type: "BOOLEAN", required: true },
    { field_key: "company_topics_discussed", field_label: "Company recommended topics discussed", field_type: "BOOLEAN", required: true },
    { field_key: "deficiencies_discussed", field_label: "Safety/Deficiencies discussed", field_type: "BOOLEAN", required: true },
    { field_key: "near_misses_discussed", field_label: "Near misses discussed", field_type: "BOOLEAN", required: true },
    { field_key: "immediate_actions_discussed", field_label: "Immediate actions discussed", field_type: "BOOLEAN", required: true },
    { field_key: "major_incidents_discussed", field_label: "Major incidents discussed", field_type: "BOOLEAN", required: true },
    { field_key: "emergency_drills_discussed", field_label: "Emergency drills discussed", field_type: "BOOLEAN", required: true },
  ],
  2: [],
  3: [
    { field_key: "permit_to_work_compliance", field_label: "Compliance with PTW (Permit To Work)", field_type: "BOOLEAN", required: true },
    { field_key: "checklist_system_compliance", field_label: "Compliance with Checklist system", field_type: "BOOLEAN", required: true },
    { field_key: "alcohol_policy", field_label: "Compliance with Alcohol policy", field_type: "BOOLEAN", required: true },
    { field_key: "risk_assessment_management", field_label: "Compliance with Risk assessment", field_type: "BOOLEAN", required: true },
    { field_key: "rest_hours", field_label: "Compliance with Rest hours", field_type: "BOOLEAN", required: true },
    { field_key: "marpol_procedure_compliance", field_label: "Compliance with MARPOL procedure", field_type: "BOOLEAN" },
    { field_key: "latest_circular_safety_alert_received", field_label: "Received Latest Circular/safety alert?", field_type: "BOOLEAN" },
    { field_key: "latest_circular_safety_alert", field_label: "Circular/alert Sr. No.", field_type: "TEXT" },
    { field_key: "best_practices", field_label: "Best practices", field_type: "TEXT" },
    ...Array.from({ length: 10 }, (_, index) => ({
      field_key: `quality_safety_topic_${index + 1}`,
      field_label: `Q&S topic ${index + 1}`,
      field_type: "TEXT",
    })),
  ],
  4: [
    { field_key: "immediate_security_concerns", field_label: "Immediate security concerns", field_type: "TEXT", required: true },
    { field_key: "security_best_practices", field_label: "Best practices", field_type: "TEXT" },
    { field_key: "cyber_security_notes", field_label: "Cyber notes", field_type: "TEXT" },
    { field_key: "seq_message", field_label: "SEQ message", field_type: "TEXT" },
  ],
  5: [
    { field_key: "kpi_review", field_label: "KPI review", field_type: "TEXT", required: true, separate_display: true },
    { field_key: "environment_best_practices", field_label: "Best practices", field_type: "TEXT" },
  ],
  6: [
    { field_key: "health_review", field_label: "Health review", field_type: "TEXT", required: true },
    { field_key: "rest_hours_compliance", field_label: "Compliance with Rest hours", field_type: "BOOLEAN", required: true },
    { field_key: "medical_certificates_healthy", field_label: "Validity of Medical certificates", field_type: "BOOLEAN", required: true },
    { field_key: "weekly_master_inspection", field_label: "Weekly Master inspection", field_type: "BOOLEAN", required: true },
    { field_key: "mess_committee_meeting", field_label: "Mess committee", field_type: "BOOLEAN", required: true },
    { field_key: "health_best_practices", field_label: "Best practices", field_type: "TEXT" },
  ],
  7: [
    { field_key: "crew_complaint_received", field_label: "Complaint received", field_type: "BOOLEAN", required: true },
    { field_key: "matter_status_resolved", field_label: "Status resolved", field_type: "BOOLEAN" },
    { field_key: "complaint_form_submitted", field_label: "Scan copy submitted", field_type: "BOOLEAN" },
    { field_key: "crew_best_practices", field_label: "Best practices", field_type: "TEXT" },
  ],
  8: [
    ...Array.from({ length: 10 }, (_, index) => ({
      field_key: `findings${index + 1}`,
      field_label: `Findings ${index + 1}`,
      field_type: "TEXT",
      required: index === 0,
    })),
    ...Array.from({ length: 10 }, (_, index) => ({
      field_key: `correctivemeasure${index + 1}`,
      field_label: `Corrective Measure ${index + 1}`,
      field_type: "TEXT",
      required: index === 0,
    })),
  ],
  9: [
    { field_key: "miscellaneous_comments", field_label: "Comments", field_type: "TEXT", required: true },
  ],
  10: [
    { field_key: "officecomments", field_label: "OFFICECOMMENTS", field_type: "TEXT", office_only: true },
    { field_key: "isreviewed", field_label: "IsReviewed", field_type: "BOOLEAN", office_only: true },
  ],
} as const;

const legacyFieldValueSchema = z.union([z.string(), z.number(), z.boolean(), z.null()]);

export const safetyScmSectionSchema = z.object({
  agenda_item_number: z.number().int().min(1).max(10),
  content: z.string().default(""),
  decision: z.string().default(""),
  legacy_fields: z.record(legacyFieldValueSchema).default({}),
  section_label: z.string(),
});

const safetyScmBaseSchema = z.object({
  ad_hoc_trigger_reason: z.string().default(""),
  chair_crew_id: z.string().default(""),
  latitude: z.string().default(""),
  location: z.string().default(""),
  longitude: z.string().default(""),
  occasion: z.enum(["M", "S"]).default("M"),
  ship_position: z.enum(["S", "P"]).default("P"),
  ship_pos_from: z.string().default(""),
  ship_pos_to: z.string().default(""),
  comm_time: z.string().default(""),
  comp_time: z.string().default(""),
  meeting_date: z.string().min(1),
  meeting_time_local: z.string().min(1),
  meeting_type: z.enum(["REGULAR", "AD_HOC"]).default("REGULAR"),
  sections: z.array(safetyScmSectionSchema).length(10),
  schema_version: z.literal(SAFETY_SCM_SCHEMA_VERSION),
  vessel_code: z.string().min(1),
  vessel_id: z.string().min(1),
  voyage_no: z.string().default(""),
});

function enforceLocationOrCoordinates(
  value: z.infer<typeof safetyScmBaseSchema>,
  context: z.RefinementCtx,
) {
  if (!value.location.trim() && (!value.latitude.trim() || !value.longitude.trim())) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Enter a location or at-sea latitude and longitude.",
      path: ["location"],
    });
  }
}

export const safetyScmSchema = safetyScmBaseSchema.superRefine(enforceLocationOrCoordinates);

export const safetyScmSubmitSchema = safetyScmBaseSchema
  .superRefine((value, context) => {
    enforceLocationOrCoordinates(value, context);
    if (value.meeting_type === "AD_HOC" && value.ad_hoc_trigger_reason.trim().length < 20) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Ad-Hoc trigger reason must be at least 20 characters.",
        path: ["ad_hoc_trigger_reason"],
      });
    }
    for (const section of value.sections) {
      if (section.agenda_item_number === 10) {
        continue;
      }
      const fieldTemplate = safetyScmLegacyFieldTemplate[
        section.agenda_item_number as keyof typeof safetyScmLegacyFieldTemplate
      ] ?? [];
      fieldTemplate.forEach((field) => {
        if (!("required" in field) || !field.required) {
          return;
        }
        const fieldValue = section.legacy_fields[field.field_key];
        if (fieldValue === null || fieldValue === undefined || fieldValue === "") {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            message: `${field.field_label} is required.`,
            path: ["sections", section.agenda_item_number - 1, "legacy_fields", field.field_key],
          });
        }
      });
    }
  });

export type SafetyScmSectionValues = z.infer<typeof safetyScmSectionSchema>;
export type SafetyScmValues = z.infer<typeof safetyScmSchema>;
export type SafetyScmSubmitValues = z.infer<typeof safetyScmSubmitSchema>;

export interface SafetyScmAgendaActionItem {
  assigned_crew_id: string | null;
  assigned_office_user_id: string | null;
  description: string;
  display_status: string;
  due_date: string | null;
  id: number;
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
  id: number;
  linked_finding_ids: number[];
  linked_incident_ids: number[];
  section_label: string;
}

export interface SafetyScmCarriedForwardItem extends SafetyScmAgendaActionItem {
  agenda_item_number: number;
  section_label: string;
  source_meeting_id: number;
  source_scm_number: string;
}

export interface SafetyScmAgendaPayload {
  carried_forward_items: SafetyScmCarriedForwardItem[];
  meeting_date: string;
  meeting_id: number;
  meeting_state: string;
  meeting_type: string;
  rows: SafetyScmAgendaRow[];
  summary: {
    carried_forward_count: number;
    current_action_item_count: number;
    open_action_item_count: number;
  };
}
