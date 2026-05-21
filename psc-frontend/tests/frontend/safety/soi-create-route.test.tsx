import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import SafetySoiCreateRoute from "../../../src/routes/safety/soi/create";

const navigateMock = vi.fn();
const toastMock = vi.fn();
const createSoiInspectionMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../src/hooks/use-toast", () => ({
  useToast: () => ({
    toast: toastMock,
  }),
}));

vi.mock("../../../src/hooks/safety/use-auth", () => ({
  useSafetyAuth: () => ({
    formIds: ["SAF_F_004"],
    hasAnySafetyAccess: () => true,
    hasForm: () => true,
    hasProcess: () => true,
    isGlobal: false,
    processIds: ["SAF_P_001"],
    role: "CO",
    user: null,
    vesselIds: ["7"],
  }),
}));

vi.mock("../../../src/hooks/use-safety", () => ({
  safetyKeys: {
    soiCompliance: (vesselId?: string) => ["safety", "soi-compliance", vesselId],
    soiInspections: () => ["safety", "soi"],
  },
  useSafetySoiCreateConfig: () => ({
    data: {
      areas: [
        {
          applicable: true,
          area_id: 3,
          area_name: "Bridge",
          due_at: "2026-05-20T00:00:00Z",
          last_inspected_at: "2026-02-20T00:00:00Z",
          map_id: 3,
          schema_version: 1,
          section_12_flag: false,
        },
        {
          applicable: true,
          area_id: 13,
          area_name: "Cross-cutting Safety & Culture",
          due_at: null,
          last_inspected_at: null,
          map_id: 13,
          schema_version: 1,
          section_12_flag: true,
        },
      ],
      assistant_candidates: [
        {
          crew_id: "2e-7",
          crew_name: "Second Engineer Seven",
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
        source_description: "SSQE baseline",
        version_label: "v1.0",
      },
      max_trainees: 3,
      safety_officer: {
        crew_id: "co-7",
        crew_name: "Chief Officer Seven",
        department: "DECK",
        rank: "CO",
        vessel_id: "7",
      },
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
      trainee_candidates: [
        {
          crew_id: "cadet-7",
          crew_name: "Cadet Seven",
          department: "DECK",
          rank: "CADET",
          vessel_id: "7",
        },
        {
          crew_id: "oiler-7",
          crew_name: "Oiler Seven",
          department: "ENGINE",
          rank: "OILER",
          vessel_id: "7",
        },
      ],
    },
    isError: false,
    isLoading: false,
  }),
}));

vi.mock("../../../src/lib/api/safety", () => ({
  safetyApi: {
    createSoiInspection: (...args: unknown[]) => createSoiInspectionMock(...args),
  },
}));

function renderRoute() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  render(
    <QueryClientProvider client={queryClient}>
      <SafetySoiCreateRoute />
    </QueryClientProvider>,
  );
}

describe("SafetySoiCreateRoute", () => {
  it("creates the inspection and routes to the paper download step without any upload field", async () => {
    createSoiInspectionMock.mockResolvedValue({ id: 42 });

    renderRoute();

    expect(screen.queryByRole("button", { name: /upload/i })).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/upload/i)).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Planned date"), {
      target: { value: "2026-05-08" },
    });
    fireEvent.change(screen.getByLabelText("Trainee slot 1"), {
      target: { value: "cadet-7" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create and continue to Download Paper" }));

    await waitFor(() => {
      expect(createSoiInspectionMock).toHaveBeenCalledWith({
        area_ids: [3, 13],
        assistant_crew_id: "2e-7",
        cycle_label: "Q2/2026",
        planned_date: "2026-05-08",
        safety_officer_crew_id: "co-7",
        section_12_included: true,
        trainee_crew_ids: ["cadet-7"],
        vessel_id: "7",
      });
    });

    expect(toastMock).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "SOI created",
        variant: "success",
      }),
    );
    expect(navigateMock).toHaveBeenCalledWith("/safety/soi/42/download");
  });
});
