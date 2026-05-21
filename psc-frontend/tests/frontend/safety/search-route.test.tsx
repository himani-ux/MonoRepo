import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety search route", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the Step 8.8 search route for users with SAF_F_005", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/search"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_005"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Safety Search" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/platform sql server full-text engine/i),
    ).toBeInTheDocument();
  });

  it("soft-blocks queries shorter than 3 characters without calling the API", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/search?q=ma"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_005"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: /search terms need at least 3 characters/i }),
    ).toBeInTheDocument();
    await waitFor(() => expect(fetchSpy).not.toHaveBeenCalled());
  });

  it("loads grouped search results when a valid query is present", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          counts: {
            INCIDENT: 1,
            NEAR_MISS: 0,
            SCM: 0,
            SOI_FINDING: 0,
          },
          groups: {
            INCIDENT: [
              {
                archived: false,
                id: 11,
                record_label: "Incident",
                record_type: "INCIDENT",
                reference: "INC/2026/301",
                route: "/safety/incidents/11/phase-3",
                snippet: "Hydraulic manifold leak observed during cargo watch handover.",
                state: "UNDER_REVIEW",
                title: "INC/2026/301",
                vessel_id: "7",
                when: "2026-04-30T08:00:00+00:00",
              },
            ],
            NEAR_MISS: [],
            SCM: [],
            SOI_FINDING: [],
          },
          include_archived: false,
          labels: {
            INCIDENT: "Incidents",
            NEAR_MISS: "Near Miss",
            SCM: "SCM",
            SOI_FINDING: "SOI Findings",
          },
          query: "manifold",
          record_type: "ALL",
          total_count: 1,
        }),
      }),
    );

    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/search?q=manifold"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_005"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByText("1 matching Safety records"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("INC/2026/301").length).toBeGreaterThan(0);
    expect(screen.getByText(/Hydraulic manifold leak observed/i)).toBeInTheDocument();
  });

  it("hydrates the archive opt-in from URL state and sends it to the API", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        counts: {
          INCIDENT: 1,
          NEAR_MISS: 0,
          SCM: 0,
          SOI_FINDING: 0,
        },
        groups: {
          INCIDENT: [
            {
              archived: true,
              id: 99,
              record_label: "Incident",
              record_type: "INCIDENT",
              reference: "INC/2023/099",
              route: "/safety/incidents/99/phase-8",
              snippet: "Archived manifold case retained inside the soft-archive window.",
              state: "CLOSED",
              title: "INC/2023/099",
              vessel_id: "7",
              when: "2023-04-30T08:00:00+00:00",
            },
          ],
          NEAR_MISS: [],
          SCM: [],
          SOI_FINDING: [],
        },
        include_archived: true,
        labels: {
          INCIDENT: "Incidents",
          NEAR_MISS: "Near Miss",
          SCM: "SCM",
          SOI_FINDING: "SOI Findings",
        },
        query: "manifold",
        record_type: "ALL",
        total_count: 1,
      }),
    });
    vi.stubGlobal("fetch", fetchSpy);

    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/search?q=manifold&include_archived=true"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_005"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    const requestedUrl = new URL(String(fetchSpy.mock.calls[0]?.[0]));
    expect(requestedUrl.searchParams.get("q")).toBe("manifold");
    expect(requestedUrl.searchParams.get("include_archived")).toBe("true");
    expect(
      screen.getByRole("checkbox", { name: /include archived records/i }),
    ).toBeChecked();

    expect(
      await screen.findByText(/including the current archive window/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Archived")).toBeInTheDocument();
    expect(router.state.location.search).toBe("?q=manifold&include_archived=true");
  });
});
