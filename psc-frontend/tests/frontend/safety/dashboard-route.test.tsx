import { fireEvent, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";
import { useSafetyDashboardPeriodStore } from "../../../src/stores/safety/dashboard-period-store";

describe("Safety dashboard route", () => {
  it("renders the Step 7.2 dashboard route for users with SAF_F_015", async () => {
    useSafetyDashboardPeriodStore.getState().reset();
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/dashboard"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_015"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Safety Intelligence Dashboard" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Safety Health Score")).toBeInTheDocument();
    expect(screen.getByText("Reporting-culture pyramid")).toBeInTheDocument();
    expect(screen.getByText("Current vessel and fleet average")).toBeInTheDocument();
    expect(screen.getByText("Fleet and vessel recurrence scan")).toBeInTheDocument();
    expect(screen.getByText("Top repeat failures over the rolling 12 months")).toBeInTheDocument();
    expect(screen.getByText("Corrective action pressure by age band")).toBeInTheDocument();
    expect(screen.getAllByText("SOI Compliance %").length).toBeGreaterThan(0);
  });

  it("switches the persisted period selector without leaving the route", async () => {
    useSafetyDashboardPeriodStore.getState().reset();
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/dashboard"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_015"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    await screen.findByRole("heading", { name: "Safety Intelligence Dashboard" });
    fireEvent.click(screen.getByRole("button", { name: "12M" }));

    expect(screen.getByText(/annual handover slice/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "12M" })).toHaveAttribute("aria-pressed", "true");
  });

  it("hides the dashboard route when the dashboard form gate is missing", () => {
    useSafetyDashboardPeriodStore.getState().reset();
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/dashboard"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Safety Intelligence Dashboard" }),
    ).not.toBeInTheDocument();
  });

  it("shows the DPA-only dashboard export preview when role and process access are present", async () => {
    useSafetyDashboardPeriodStore.getState().reset();
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/dashboard"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_015"], processIds: ["SAF_P_023"], role: "DPA", vesselIds: ["7"] }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    await screen.findByRole("heading", { name: "Safety Intelligence Dashboard" });
    expect(screen.getByRole("button", { name: "Preview PDF export" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Preview Excel export" }));
    expect(screen.getByText(/"format": "excel"/i)).toBeInTheDocument();
  });

  it("keeps the dashboard export preview hidden for FM readers", async () => {
    useSafetyDashboardPeriodStore.getState().reset();
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/dashboard"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_015"], processIds: ["SAF_P_023"], role: "FM", vesselIds: ["7"] }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    await screen.findByRole("heading", { name: "Safety Intelligence Dashboard" });
    expect(screen.queryByRole("button", { name: "Preview PDF export" })).not.toBeInTheDocument();
    expect(screen.getByText(/export-blocked in V1/i)).toBeInTheDocument();
  });
});
