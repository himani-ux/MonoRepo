import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety admin routes", () => {
  it("renders the DPA-only Step 7.7 admin landing when SAF_F_018 is present", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/admin"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_018"], role: "DPA" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Safety Admin" })).toBeInTheDocument();
    expect(screen.getByText("Taxonomy Admin")).toBeInTheDocument();
    expect(screen.getByText("Case Study Library")).toBeInTheDocument();
  });

  it("hides the admin routes when the user is not DPA", () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/admin"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_018"], role: "FM" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(screen.queryByRole("heading", { name: "Safety Admin" })).not.toBeInTheDocument();
  });

  it("renders the taxonomy shell with the stronger SAF_P_018 and SAF_P_019 splits", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/admin/taxonomy"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_018"], role: "DPA" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Taxonomy Admin" })).toBeInTheDocument();
    expect(screen.getByText("M-SCAT taxonomy")).toBeInTheDocument();
    expect(screen.getByText("SOI checklist versions")).toBeInTheDocument();
    expect(screen.getAllByText("SAF_P_018").length).toBeGreaterThan(0);
    expect(screen.getAllByText("SAF_P_019").length).toBeGreaterThan(0);
  });

  it("renders the seeded case-study route with Navigator and Sinkfast", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/admin/case-studies"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_018"], role: "DPA" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(await screen.findByRole("heading", { name: /Navigator \+ Sinkfast/i })).toBeInTheDocument();
    expect(screen.getByText("Navigator")).toBeInTheDocument();
    expect(screen.getByText("Sinkfast")).toBeInTheDocument();
  });
});
