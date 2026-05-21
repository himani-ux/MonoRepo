import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety reopen route", () => {
  it("renders the re-open route for users with SAF_F_001 and SAF_P_008", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/incidents/42/reopen"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"], processIds: ["SAF_P_008"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Re-open Closed Incident" }),
    ).toBeInTheDocument();
  });
});
