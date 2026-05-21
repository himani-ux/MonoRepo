import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  PermissionGate,
  ProcessGate,
} from "../../../src/components/safety/shared/permission-gate";
import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";

describe("Safety permission gates", () => {
  it("renders children when the form id is present", () => {
    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
        <PermissionGate formId="SAF_F_001">
          <span>Incident screen</span>
        </PermissionGate>
      </SafetyAuthProvider>,
    );

    expect(screen.getByText("Incident screen")).toBeInTheDocument();
  });

  it("renders null when the form id is absent", () => {
    const { container } = render(
      <SafetyAuthProvider value={{ formIds: [] }}>
        <PermissionGate formId="SAF_F_001">
          <span>Hidden incident screen</span>
        </PermissionGate>
      </SafetyAuthProvider>,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("respects nested process gates", () => {
    render(
      <SafetyAuthProvider
        value={{ formIds: ["SAF_F_001"], processIds: ["SAF_P_004"] }}
      >
        <PermissionGate formId="SAF_F_001">
          <ProcessGate processId="SAF_P_004">
            <button type="button">Approve</button>
          </ProcessGate>
        </PermissionGate>
      </SafetyAuthProvider>,
    );

    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
  });
});

