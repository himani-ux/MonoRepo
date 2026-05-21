import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety Phase 2 routes", () => {
  it("renders the phase 2 route for users with SAF_F_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/incidents/42/phase-2"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Notifications + Resource Allocation" }),
    ).toBeInTheDocument();
  });
});
