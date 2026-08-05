import { describe, expect, it } from "vitest";

import {
  SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION,
  safetyIncidentPhase1SubmitSchema,
  type SafetyIncidentPhase1SubmitValues,
} from "./incident-phase1";

function baseSubmitValues(
  overrides: Partial<SafetyIncidentPhase1SubmitValues> = {},
) {
  return {
    awaiting_daily_report_match: false,
    narrative: "Incident narrative ".repeat(14),
    office_notified: false,
    reporter_device_fingerprint: "fp:test-device",
    reporter_name: "Praweepat Hawanit",
    reporter_rank: "MASTER",
    reporter_user_id: "KSM0090",
    risk_band: "YELLOW",
    schema_version: SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION,
    vessel_id: "ARY",
    ...overrides,
  };
}

function expectIssueFor(
  result: ReturnType<typeof safetyIncidentPhase1SubmitSchema.safeParse>,
  path: string,
  message: string,
) {
  if (result.success) {
    throw new Error(`Expected ${path} validation to fail.`);
  }

  expect(result.error.issues).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        message,
        path: [path],
      }),
    ]),
  );
}

describe("safetyIncidentPhase1SubmitSchema", () => {
  it("rejects future report times before submitting to the API", () => {
    const futureReportTime = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

    const result = safetyIncidentPhase1SubmitSchema.safeParse(
      baseSubmitValues({
        reported_at: futureReportTime,
      }),
    );

    expectIssueFor(result, "reported_at", "Report time cannot be in the future.");
  });

  it("rejects future incident times before submitting to the API", () => {
    const futureIncidentTime = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

    const result = safetyIncidentPhase1SubmitSchema.safeParse(
      baseSubmitValues({
        occurred_at: futureIncidentTime,
      }),
    );

    expectIssueFor(result, "occurred_at", "Incident time cannot be in the future.");
  });

  it("rejects incident times after the report time", () => {
    const result = safetyIncidentPhase1SubmitSchema.safeParse(
      baseSubmitValues({
        occurred_at: "2026-06-23T12:00:00.000Z",
        reported_at: "2026-06-23T10:00:00.000Z",
      }),
    );

    expectIssueFor(result, "occurred_at", "Incident time cannot be after report time.");
  });
});
