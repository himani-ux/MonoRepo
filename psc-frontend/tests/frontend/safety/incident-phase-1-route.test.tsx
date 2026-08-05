import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useRoutes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider, type SafetyAuthUser } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

vi.mock("@/components/layout/root-layout", () => ({
  RootLayout: ({ children }: { children: ReactNode }) => (
    <div data-testid="root-layout">{children}</div>
  ),
}));

vi.mock("../../../src/routes/safety/incident/new", () => ({
  default: () => <h1>Tell Us What Happened</h1>,
}));

vi.mock("../../../src/routes/safety/incident/[id]/phase-1", () => ({
  default: () => <h1>Tell Us What Happened</h1>,
}));

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

function renderSafetyRoute(pathname: string, auth: Partial<SafetyAuthUser> = {}) {
  return render(
    <MemoryRouter initialEntries={[pathname]}>
      <SafetyAuthProvider
        value={{
          formIds: ["SAF_F_001"],
          processIds: ["SAF_P_001"],
          role: "MASTER",
          ...auth,
        }}
      >
        <Routes>
          <Route path="/safety/*" element={<SafetyRoutesHarness />} />
        </Routes>
      </SafetyAuthProvider>
    </MemoryRouter>,
  );
}

describe("Safety Phase 1 routes", () => {
  it("renders the create route for users with SAF_F_001 and SAF_P_001", async () => {
    renderSafetyRoute("/safety/incidents/create");

    expect(
      await screen.findByRole("heading", { name: "Tell Us What Happened" }),
    ).toBeInTheDocument();
  });

  it("renders the resume route for users with SAF_F_001", async () => {
    renderSafetyRoute("/safety/incidents/42/phase-1");

    expect(
      await screen.findByRole("heading", { name: "Tell Us What Happened" }),
    ).toBeInTheDocument();
  });

  it("hides the create route when SAF_P_001 is missing", () => {
    renderSafetyRoute("/safety/incidents/create", {
      processIds: [],
      role: "MASTER",
    });

    expect(
      screen.queryByRole("heading", { name: "Tell Us What Happened" }),
    ).not.toBeInTheDocument();
  });
});
