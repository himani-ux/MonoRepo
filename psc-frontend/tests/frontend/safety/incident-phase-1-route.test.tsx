import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety Phase 1 routes", () => {
  it("renders the create route for users with SAF_F_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/incidents/create"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_001"], processIds: ["SAF_P_001"], role: "MASTER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Intake + Scene Control" }),
    ).toBeInTheDocument();
  });

  it("renders the resume route for users with SAF_F_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/incidents/42/phase-1"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Intake + Scene Control" }),
    ).toBeInTheDocument();
  });

  it("hides the create route when SAF_P_001 is missing", () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/incidents/create"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Intake + Scene Control" }),
    ).not.toBeInTheDocument();
  });
});
