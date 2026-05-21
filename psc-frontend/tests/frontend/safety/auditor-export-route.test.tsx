import { fireEvent, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety auditor export route", () => {
  it("renders the auditor export route for Master users with SAF_F_020", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/admin/auditor-export"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_020"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Auditor Leave-Behind ZIP" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Auditor Export Configurator" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("SOI"));
    fireEvent.click(screen.getByRole("button", { name: "Build Demo Bundle Plan" }));

    expect(screen.getByText(/"record_types": \[/)).toBeInTheDocument();
    expect(screen.getByText(/"SOI"/)).toBeInTheDocument();
  });

  it("hides the auditor export route when the dedicated form gate is missing", () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/admin/auditor-export"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_006"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Auditor Leave-Behind ZIP" }),
    ).not.toBeInTheDocument();
  });

  it("hides the auditor export route when the role gate is neither Master nor DPA", () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/admin/auditor-export"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_020"], role: "FM" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Auditor Leave-Behind ZIP" }),
    ).not.toBeInTheDocument();
  });
});
