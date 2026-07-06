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

vi.mock("../../../src/routes/safety/incident/[id]/phase-8", () => ({
  default: () => <h1>Loss Evaluation</h1>,
}));

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

describe("Safety Phase 7 route", () => {
  it("renders Loss Evaluation on the current phase-6 compatibility path", async () => {
    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-6"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"], role: "MASTER" }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Loss Evaluation" }),
    ).toBeInTheDocument();
  });
});
