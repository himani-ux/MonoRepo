import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety audit route", () => {
  it("renders the audit route for users with SAF_F_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/incidents/42/audit"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Incident Audit Trail" }),
    ).toBeInTheDocument();
  });
});
