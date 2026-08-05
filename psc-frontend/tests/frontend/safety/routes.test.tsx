import { render, screen } from "@testing-library/react";
import { createMemoryRouter, MemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetySidebarGroup } from "../../../src/components/safety/shared/safety-sidebar-group";
import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety route scaffold", () => {
  it("renders /safety/incidents when the user has SAF_F_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/incidents"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Safety Incidents" }),
    ).toBeInTheDocument();
  });

  it("renders /safety/incidents/create when the user has SAF_F_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/incidents/create"],
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

  it("renders /safety/incidents/:id/phase-2 when the user has SAF_F_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/incidents/42/phase-2"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Notifications + Resource Allocation" }),
    ).toBeInTheDocument();
  });

  it("returns null for the sidebar group when the user has no safety access", () => {
    const { container } = render(
      <SafetyAuthProvider value={{ formIds: [] }}>
        <SafetySidebarGroup />
      </SafetyAuthProvider>,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("keeps auditor export in the sidebar without showing the broad admin item", () => {
    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_018", "SAF_F_020"] }}>
        <MemoryRouter>
          <SafetySidebarGroup />
        </MemoryRouter>
      </SafetyAuthProvider>,
    );

    expect(screen.getByRole("link", { name: "Auditor Export" })).toHaveAttribute(
      "href",
      "/safety/admin/auditor-export",
    );
    expect(screen.queryByRole("link", { name: "Admin" })).not.toBeInTheDocument();
  });
});
