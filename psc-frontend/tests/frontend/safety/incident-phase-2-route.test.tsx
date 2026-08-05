import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useRoutes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

vi.mock("@/components/layout/root-layout", () => ({
  RootLayout: ({ children }: { children: ReactNode }) => (
    <div data-testid="root-layout">{children}</div>
  ),
}));

vi.mock("../../../src/routes/safety/incident/[id]/phase-5", () => ({
  default: () => <h1>RCA (Root Cause Analysis)</h1>,
}));

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

describe("Safety Phase 2 route", () => {
  it("renders RCA on the current phase-2 path", async () => {
    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-2"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"], role: "MASTER" }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "RCA (Root Cause Analysis)" }),
    ).toBeInTheDocument();
  });
});
