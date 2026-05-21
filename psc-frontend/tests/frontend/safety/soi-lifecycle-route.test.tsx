import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import SafetySoiFindingsRoute from "../../../src/routes/safety/soi/[id]/findings/index";
import SafetySoiIndexRoute from "../../../src/routes/safety/soi";

const authState = vi.hoisted(() => ({
  hasProcess: (processId: string) => processId === "SAF_P_001",
  role: "CO",
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ id: "42" }),
  };
});

vi.mock("../../../src/hooks/safety/use-auth", () => ({
  useSafetyAuth: () => ({
    formIds: ["SAF_F_004"],
    hasAnySafetyAccess: () => true,
    hasForm: () => true,
    hasProcess: authState.hasProcess,
    isGlobal: false,
    processIds: ["SAF_P_001", "SAF_P_014"],
    role: authState.role,
    user: null,
    vesselIds: ["7"],
  }),
}));

vi.mock("../../../src/hooks/use-safety", () => ({
  useSafetySoiCompliance: () => ({
    data: {
      amber_area_count: 1,
      applicable_area_count: 4,
      areas: [],
      compliance_percent: 75,
      display_value: "75%",
      inspected_area_count: 3,
      label: "SOI Compliance %",
      overdue_area_count: 0,
      status: "AMBER",
      vessel_id: "7",
    },
    error: null,
    isLoading: false,
  }),
  useSafetySoiFindings: () => ({
    data: [
      {
        area_id: 3,
        assigned_crew_id: "bosun-7",
        description: "Bridge wing light fitting loose.",
        due_date: null,
        id: 901,
        inspection_id: 42,
        is_repeat: false,
        master_approval_state: null,
        master_counter_signature: null,
        pending_closure_signature: null,
        photo_attachment_path: "vessel-7/soi/light.jpg",
        priority: "MED",
        repeat_badge_text: null,
        repeat_occurrence_count: 0,
        severity: "MED",
        status: "OPEN",
        title: "Loose light fitting",
      },
    ],
    error: null,
    isLoading: false,
  }),
  useSafetySoiInspection: () => ({
    data: {
      assistant_crew_id: "2e-7",
      checklist_format: "PDF",
      checklist_generated_at: null,
      checklist_unique_id: "SOI-0000007-20260508-0042",
      checklist_version: null,
      closed_at: null,
      created_by: "co-7",
      created_date: "2026-05-08T10:00:00Z",
      cycle_label: "Q2/2026",
      fieldwork_started_at: null,
      id: 42,
      inspection_reference: "SOI/ABC/26/42",
      lost_paper_flag: false,
      lost_paper_note: null,
      master_crew_id: "master-7",
      planned_date: "2026-05-08",
      reported_at: "2026-05-08T14:00:00Z",
      safety_officer_crew_id: "co-7",
      safety_officer_department: "DECK",
      schema_version: 1,
      section_12_included: true,
      selected_areas: [
        {
          area_id: 3,
          area_name: "Bridge",
          display_order: 1,
          inspected: true,
          inspection_id: 42,
          last_inspected_at: "2026-05-08T13:00:00Z",
          notes: null,
          schema_version: 1,
          section_12_flag: false,
          selection_id: 3001,
        },
      ],
      state: "REPORTED",
      trainees: [],
      updated_by: "co-7",
      updated_date: "2026-05-08T14:00:00Z",
      vessel_id: "7",
    },
    error: null,
    isLoading: false,
  }),
  useSafetySoiInspections: () => ({
    data: [
      {
        assistant_crew_id: "2e-7",
        checklist_format: null,
        checklist_generated_at: null,
        checklist_unique_id: null,
        checklist_version: null,
        closed_at: null,
        created_by: "co-7",
        created_date: "2026-05-08T10:00:00Z",
        cycle_label: "Q2/2026",
        fieldwork_started_at: null,
        id: 42,
        inspection_reference: "SOI/ABC/26/42",
        lost_paper_flag: false,
        lost_paper_note: null,
        master_crew_id: null,
        planned_date: "2026-05-08",
        reported_at: null,
        safety_officer_crew_id: "co-7",
        safety_officer_department: "DECK",
        schema_version: 1,
        section_12_included: true,
        selected_areas: [],
        state: "PLANNED",
        trainees: [],
        updated_by: "co-7",
        updated_date: "2026-05-08T10:00:00Z",
        vessel_id: "7",
      },
    ],
    error: null,
    isLoading: false,
  }),
  safetyKeys: {
    soiFindings: () => ["safety", "soi", "findings"],
    soiInspection: () => ["safety", "soi", "detail"],
    soiInspections: () => ["safety", "soi"],
  },
}));

describe("SOI lifecycle navigation", () => {
  function renderRoute(ui: ReactElement) {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{ui}</MemoryRouter>
      </QueryClientProvider>,
    );
  }

  it("exposes the download paper step from the SOI register", async () => {
    authState.role = "CO";
    authState.hasProcess = (processId: string) => processId === "SAF_P_001" || processId === "SAF_P_014";

    renderRoute(<SafetySoiIndexRoute />);

    const downloadLink = await screen.findByRole("link", { name: "Download paper" });
    expect(downloadLink).toHaveAttribute("href", "/safety/soi/42/download");
    expect(screen.getByRole("link", { name: "Start inspection" })).toHaveAttribute(
      "href",
      "/safety/soi/create",
    );
  });

  it("hides Start Inspection for non-SO users even when SAF_P_001 is present", async () => {
    authState.role = "MASTER";
    authState.hasProcess = (processId: string) => processId === "SAF_P_001";

    renderRoute(<SafetySoiIndexRoute />);

    await screen.findByRole("heading", { name: "Current SOI register" });
    expect(screen.queryByRole("link", { name: "Start inspection" })).not.toBeInTheDocument();
  });

  it("exposes submit-for-master-closure from the findings flow for ship officers", async () => {
    authState.role = "CO";
    authState.hasProcess = (processId: string) => processId === "SAF_P_001" || processId === "SAF_P_014";

    renderRoute(<SafetySoiFindingsRoute />);

    expect(await screen.findByRole("link", { name: "Download paper" })).toHaveAttribute(
      "href",
      "/safety/soi/42/download",
    );
    expect(screen.getByRole("link", { name: "Submit for Master closure" })).toHaveAttribute(
      "href",
      "/safety/soi/42/findings/901",
    );
  });

  it("exposes the close-event step from the findings flow for Master once reporting is complete", async () => {
    authState.role = "MASTER";
    authState.hasProcess = (processId: string) => processId === "SAF_P_001" || processId === "SAF_P_004" || processId === "SAF_P_015";

    renderRoute(<SafetySoiFindingsRoute />);

    expect(await screen.findByRole("link", { name: "Close SOI event" })).toHaveAttribute(
      "href",
      "/safety/soi/42/close",
    );
  });
});
