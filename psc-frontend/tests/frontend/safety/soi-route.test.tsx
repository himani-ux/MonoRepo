import { fireEvent, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

describe("Safety SOI routes", () => {
  it("renders the SOI register for users with SAF_F_004", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_004"], role: "DPA" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Safety Officer Inspections" }),
    ).toBeInTheDocument();
    expect(screen.getByText("SOI Compliance %")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Current SOI register" }),
    ).toBeInTheDocument();
  });

  it("renders the SOI create route for CO users with SAF_P_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/create"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_001"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Create SOI" }),
    ).toBeInTheDocument();
    expect(screen.getByText("v1.0")).toBeInTheDocument();
    expect(
      screen.getByText("Cross-cutting Safety & Culture not yet covered this quarter - include now?"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Cross-functional assistant" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Trainee participation" })).toBeInTheDocument();
  });

  it("renders the SOI pick-areas route for 2/E users with SAF_P_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/pick-areas"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_001"], role: "2/E" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SOI Pick Areas" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Section 12 already carried for Q2\/2026/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Picked areas" })).toBeInTheDocument();
  });

  it("renders the SOI download route for CO users with SAF_P_001", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/download"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_001"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Download SOI Checklist" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Paper-first guidance" })).toBeInTheDocument();
    expect(screen.getByText("No scan upload")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lost paper? Re-download" })).toBeInTheDocument();
  });

  it("requires a reason before closing the SOI lost-paper recovery modal", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/download"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_001"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "Lost paper? Re-download" }));
    fireEvent.click(screen.getByRole("button", { name: "Log loss and re-download" }));

    expect(screen.getByText("Recovery reason is required.")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Reason"), {
      target: { value: "Checklist was damaged during field walkthrough." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Log loss and re-download" }));

    expect(screen.queryByText("Recovery reason is required.")).not.toBeInTheDocument();
    expect(
      screen.getByText(/Demo recovery note: Checklist was damaged during field walkthrough\./),
    ).toBeInTheDocument();
  });

  it("renders the SOI close route for Master and records a demo close action", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/close"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_004"], role: "MASTER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SOI Close Event" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Master close package" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Close SOI event" }));

    expect(
      screen.getByText(
        "Demo SOI closed. Crew rotation coverage now shows 50% of onboard crew have accompanied at least one inspection in the last 12 months.",
      ),
    ).toBeInTheDocument();
  });

  it("renders the SOI applicability request route for Master with the dedicated applicability gate", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/applicability/request"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_013"], processIds: ["SAF_P_016"], role: "MASTER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SOI Applicability Request" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Master request package" })).toBeInTheDocument();
    expect(
      screen.getByText("Requires DPA approval before the area leaves the SOI compliance counter."),
    ).toBeInTheDocument();
  });

  it("renders the SOI applicability approval route for DPA and records a demo approval action", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/applicability/approve"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_013"], processIds: ["SAF_P_017"], role: "DPA" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SOI Applicability Approval" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve request" }));

    expect(
      screen.getByText("Demo approval captured. The vessel area map flips only after this DPA action."),
    ).toBeInTheDocument();
  });

  it("renders the SOI findings route for CO users with SAF_P_002", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/findings"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_002"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SOI Findings Register" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Checklist ID: SOI-0000007-20260501-0007")).toBeInTheDocument();
    expect(screen.getByText("Active findings for SOI/ABC/26/07")).toBeInTheDocument();
    expect(screen.queryByText(/Active findings for inspection #42/i)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Add Finding" })).toBeInTheDocument();
    expect(screen.getByText(/2 of 4 areas complete/i)).toBeInTheDocument();
  });

  it("opens the incident-worthy nudge after a HIGH severity finding has photo evidence", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/findings/create"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_002"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Create SOI Finding" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "SOI context" })).toBeInTheDocument();
    expect(screen.getByLabelText("Paper checklist unique ID")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "HIGH" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save finding" }));

    expect(
      screen.getByText("HIGH-severity SOI findings require >=1 photo."),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Photo attachment path"), {
      target: { value: "vessel-7/soi/bridge-marker-faded.jpg" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save finding" }));

    expect(await screen.findByRole("heading", { name: "This looks incident-worthy" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Create Incident" }));
    expect(
      screen.getByText(/Demo incident prefill opened from Area/i),
    ).toBeInTheDocument();
  });

  it("blocks life-threat findings until Incident or Near Miss escalation is selected", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/findings/create"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_002"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Create SOI Finding" }),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "HIGH" },
    });
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Confined space gas leak" },
    });
    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "A gas leak was detected inside a confined space beside energized equipment." },
    });
    fireEvent.change(screen.getByLabelText("Photo attachment path"), {
      target: { value: "vessel-7/soi/confined-space-gas-leak.jpg" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save finding" }));

    expect(
      screen.getByText("Life-threat findings must escalate through Incident or Near Miss before save can continue."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Create Near Miss" }));
    fireEvent.click(screen.getByRole("button", { name: "Save finding" }));

    expect(
      screen.getByText(/Parallel NEAR_MISS escalation queued for DPA\/FM notification/i),
    ).toBeInTheDocument();
  });

  it("lets the Safety Officer mark a finding pending closure on the new detail route", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/findings/901"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_014"], role: "CO" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SOI Finding Closure" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Repeat - 2nd occurrence")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Safety Officer typed name"), {
      target: { value: "Chief Officer Arun" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Mark pending closure" }));

    expect(
      screen.getByText("Demo pending-closure signature captured and routed to Master for counter-sign."),
    ).toBeInTheDocument();
    expect(screen.getByText("Pending Closure")).toBeInTheDocument();
  });

  it("lets Master counter-sign and close a pending SOI finding", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/findings/902"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_015"], role: "MASTER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SOI Finding Closure" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve closure" }));

    expect(screen.getByText("MASTER_APPROVED")).toBeInTheDocument();
    expect(
      screen.getByText("Demo finding closed after Master counter-signature."),
    ).toBeInTheDocument();
  });

  it("renders the SOI summary PDF route for users with SAF_P_023", async () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/42/pdf"],
    });

    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_004"], processIds: ["SAF_P_023"], role: "MASTER" }}
      >
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "SOI Summary PDF" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Summary Structure" })).toBeInTheDocument();
    expect(screen.getByText(/Paper checklist: unique-ID SOI-0000007-20260505-0014/i)).toBeInTheDocument();
  });

  it("hides the SOI create route when SAF_P_001 is missing", () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/safety/soi/create"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_004"], role: "CO" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Create SOI" }),
    ).not.toBeInTheDocument();
  });
});
