import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { resolveAuthorityRole } from "../../../src/components/safety/near-miss/near-miss-workspace";
import { safetyRoutes } from "../../../src/routes/safety";

const nearMissFixture = vi.hoisted(() => ({
  id: 42,
  incident_number: "DRAFT-ABC/2026/T001",
  near_miss_priority: "LOW",
  occurred_at: "2026-05-13T00:00:00Z",
  record_type: "NEAR_MISS",
  reported_at: "2026-05-13T01:00:00Z",
  reporter_name: "Anonymous Reporter",
  schema_version: 1,
  state: "TRIAGED",
  vessel_id: "7",
}));

const authState = vi.hoisted(() => ({
  hasProcess: (processId: string) => false,
  role: "MASTER" as string | undefined,
  user: {
    form_ids: ["SAF_F_002"],
    full_name: "Master User",
    process_ids: [] as string[],
    rank: "MASTER",
    role: "MASTER",
    role_name: "MASTER",
    safety_role_name: "MASTER",
  },
}));

vi.mock("@/components/layout/root-layout", () => ({
  RootLayout: ({ children }: { children: ReactNode }) => (
    <div data-testid="root-layout">{children}</div>
  ),
}));

vi.mock("../../../src/hooks/use-auth", () => ({
  useAuth: () => authState,
}));

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => authState,
}));

vi.mock("../../../src/hooks/use-safety", () => ({
  useSafetyNearMisses: () => ({
    data: [nearMissFixture],
    error: null,
    isLoading: false,
  }),
}));

vi.mock("../../../src/lib/api/safety", async () => {
  const actual = await vi.importActual<typeof import("../../../src/lib/api/safety")>(
    "../../../src/lib/api/safety",
  );
  return {
    ...actual,
    safetyApi: {
      ...actual.safetyApi,
      getNearMiss: vi.fn().mockResolvedValue(nearMissFixture),
      getNearMissAnalysis: vi.fn().mockResolvedValue({
        analysis_mode: "FACT_TREE",
        facts: [],
        near_miss: nearMissFixture,
        requirements: {},
      }),
      getNearMissFleetAlert: vi.fn().mockResolvedValue({
        draft: {
          anonymised: true,
          body: "Fleet alert draft must be issued within 7 days.",
          due_by: "2026-05-20T00:00:00Z",
          title: "Near Miss Fleet Alert",
        },
        issued: false,
        near_miss: nearMissFixture,
        recipients: [],
      }),
      getNearMissClosureSummary: vi.fn().mockResolvedValue({
        near_miss: nearMissFixture,
        ready_to_close: true,
      }),
      getReferenceIncidentTypes: vi.fn().mockResolvedValue([]),
      getReferenceLossTypes: vi.fn().mockResolvedValue([]),
      getReferenceMscat: vi.fn().mockResolvedValue([]),
    },
  };
});

function buildRouter(initialEntry: string) {
  return createMemoryRouter(
    [
      {
        path: "/safety/*",
        children: safetyRoutes,
      },
    ],
    {
      initialEntries: [initialEntry],
    },
  );
}

describe("Safety near-miss routes", () => {
  it("renders the near-miss list for users with SAF_F_002", async () => {
    const router = buildRouter("/safety/near-miss");

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_002"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Near Miss Register" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Anonymous Reporter")).toBeInTheDocument();
  });

  it("renders the create route for any-rank users with SAF_P_001", async () => {
    const router = buildRouter("/safety/near-miss/create");

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_002"], processIds: ["SAF_P_001"], role: "WIPER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Create Near Miss" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/5 submissions per vessel-local day/i),
    ).toBeInTheDocument();
  });

  it("hides the create route when SAF_P_001 is missing", () => {
    const router = buildRouter("/safety/near-miss/create");

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_002"], role: "WIPER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Create Near Miss" }),
    ).not.toBeInTheDocument();
  });

  it("renders the triage route for DPA users with SAF_P_002", async () => {
    const router = buildRouter("/safety/near-miss/42/triage");

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_002"], processIds: ["SAF_P_002"], role: "DPA" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Near Miss Triage" }),
    ).toBeInTheDocument();
  });

  it("renders the fleet-alert route for DPA users with SAF_P_024", async () => {
    const router = buildRouter("/safety/near-miss/42/fleet-alert");

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_002"], processIds: ["SAF_P_024"], role: "DPA" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Near Miss Fleet Alert" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Fleet Alert" })).toBeInTheDocument();
  });

  it("hides the triage route when SAF_P_002 is missing", () => {
    const router = buildRouter("/safety/near-miss/42/triage");

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_002"], role: "DPA" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Near Miss Triage" }),
    ).not.toBeInTheDocument();
  });

  it("hides the fleet-alert route when SAF_P_024 is missing", () => {
    const router = buildRouter("/safety/near-miss/42/fleet-alert");

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_002"], role: "DPA" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Near Miss Fleet Alert" }),
    ).not.toBeInTheDocument();
  });

  it("renders the analysis route for users with SAF_F_002", async () => {
    const router = buildRouter("/safety/near-miss/42/analysis");

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_002"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Near Miss Fact Analysis" }),
    ).toBeInTheDocument();
  });

  it("renders the closure route for users with SAF_F_002", async () => {
    const router = buildRouter("/safety/near-miss/42/closure");

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_002"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Near Miss Closure" }),
    ).toBeInTheDocument();
  });

  it("resolves generic vessel master auth role to Master authority for LOW closure", () => {
    expect(
      resolveAuthorityRole(
        {
          process_ids: ["SAF_P_004"],
          rank: "MASTER",
          role: "VESSEL_MASTER",
          role_name: "MASTER",
          safety_role_name: "MASTER",
        },
        "VESSEL_MASTER",
      ),
    ).toBe("MASTER");
    expect(resolveAuthorityRole({ role: "VESSEL_MASTER" }, "VESSEL_MASTER")).toBe("MASTER");
  });
});
