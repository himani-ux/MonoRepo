import { describe, expect, it } from "vitest";

import {
  SAFETY_SCM_SCHEMA_VERSION,
  safetyScmSectionTemplate,
  safetyScmSubmitSchema,
} from "./scm";

const requiredLegacyFields: Record<number, Record<string, string | boolean>> = {
  1: {
    company_topics_discussed: true,
    deficiencies_discussed: true,
    emergency_drills_discussed: true,
    immediate_actions_discussed: true,
    major_incidents_discussed: true,
    near_misses_discussed: true,
    previous_minutes_reviewed: true,
  },
  2: {
    alcohol_policy: true,
    checklist_system_compliance: true,
    permit_to_work_compliance: true,
    rest_hours: true,
    risk_assessment_management: true,
  },
  3: {
    immediate_security_concerns: "No immediate security concerns.",
  },
  5: {
    health_review: "Health status reviewed.",
    medical_certificates_healthy: true,
    mess_committee_meeting: true,
    weekly_master_inspection: true,
  },
  6: {
    crew_complaint_received: false,
  },
  7: {
    correctivemeasure1: "No corrective measure required.",
    findings1: "No PSC findings raised.",
  },
  8: {
    miscellaneous_comments: "Meeting minutes captured.",
  },
};

function buildSections() {
  return safetyScmSectionTemplate.map((section) => ({
    agenda_item_number: section.agenda_item_number,
    content: "",
    decision: "",
    legacy_fields: requiredLegacyFields[section.agenda_item_number] ?? {},
    section_label: section.section_label,
  }));
}

function buildPayload(overrides: Record<string, unknown> = {}) {
  return {
    ad_hoc_trigger_reason: "",
    chair_crew_id: "master-7",
    comm_time: "10:00",
    comp_time: "",
    latitude: "",
    location: "Mumbai",
    longitude: "",
    meeting_date: "2026-09-01",
    meeting_time_local: "10:00",
    meeting_type: "REGULAR",
    occasion: "M",
    schema_version: SAFETY_SCM_SCHEMA_VERSION,
    sections: buildSections(),
    ship_pos_from: "",
    ship_pos_to: "",
    ship_position: "P",
    vessel_code: "ARY",
    vessel_id: "vessel-1",
    voyage_no: "",
    ...overrides,
  };
}

describe("safetyScmSubmitSchema", () => {
  it("allows blank coordinates when a location is entered", () => {
    const result = safetyScmSubmitSchema.safeParse(buildPayload());

    expect(result.success).toBe(true);
  });

  it("rejects non-numeric coordinates before submit", () => {
    const result = safetyScmSubmitSchema.safeParse(
      buildPayload({
        latitude: "north",
        longitude: "103.851959",
      }),
    );

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues.map((issue) => issue.message)).toContain(
        "Latitude must be in decimal degrees, e.g. 1.290270. Use a minus sign for south; do not enter N/S letters.",
      );
    }
  });
});
