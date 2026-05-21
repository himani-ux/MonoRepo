import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety SCM routes", () => {
  it("renders the SCM list for users with SAF_F_003", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_003"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Safety Committee Meetings" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Current cadence" }),
    ).toBeInTheDocument();
  });

  it("renders the Regular SCM create route for CO users with SAF_P_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/create-regular"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_003"], processIds: ["SAF_P_001"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Create Regular SCM" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/10-section meeting record/i)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "SOI -> SCM auto-feed" }),
    ).toBeInTheDocument();
  });

  it("renders the Ad-Hoc SCM create route for Master users with SAF_P_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/create-adhoc"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_003"], processIds: ["SAF_P_001"], role: "MASTER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Create Ad-Hoc SCM" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Ad-Hoc trigger reason")).toBeInTheDocument();
  });

  it("hides the Regular SCM create route when the role gate is not CO", () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/create-regular"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_003"], processIds: ["SAF_P_001"], role: "MASTER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Create Regular SCM" }),
    ).not.toBeInTheDocument();
  });

  it("hides the Ad-Hoc SCM create route when the role gate is not Master", () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/create-adhoc"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_003"], processIds: ["SAF_P_001"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Create Ad-Hoc SCM" }),
    ).not.toBeInTheDocument();
  });

  it("renders the SCM detail route for users with SAF_F_003", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/42"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_003"], role: "DPA" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SCM Detail" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Closed-Since-Last SCM Summary" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "New SOI findings since last SCM" }),
    ).toBeInTheDocument();
  });

  it("renders the SCM attendance route for users with SAF_F_003", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/42/attendance"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_003"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SCM Attendance" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/warn, don't block/i)).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
  });

  it("renders the SCM agenda route for CO users with SAF_P_002", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/42/agenda"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_003"], processIds: ["SAF_P_002"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SCM Agenda" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Agenda + decisions" })).toBeInTheDocument();
    expect(screen.getAllByRole("table")).not.toHaveLength(0);
  });

  it("renders the SCM sign-off route for Master users with SAF_P_004", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/42/signoff"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_003"], processIds: ["SAF_P_004"], role: "MASTER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SCM Sign-Off" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sign-off preflight" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Master signature" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Overdue SOI hard block" })).toBeInTheDocument();
  });

  it("renders the Closed-Since-Last SCM route for users with SAF_F_003", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/42/closed-since-last"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_003"], role: "DPA" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Closed-Since-Last SCM" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Closed-Since-Last SCM Summary" }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("table")).not.toHaveLength(0);
  });

  it("renders the SCM PDF route for users with SAF_P_023", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/scm/42/pdf"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_003"], processIds: ["SAF_P_023"], role: "MASTER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "10-Section Legacy PDF" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Legacy Section Order" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Closed-Since-Last SCM Summary/i)).toBeInTheDocument();
  });
});
