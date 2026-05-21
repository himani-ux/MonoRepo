import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SafetyAnonymityBadge } from "../../../src/components/safety/shared/anonymity-badge";

describe("SafetyAnonymityBadge", () => {
  it("shows the masked state for non-DPA/FM viewers", () => {
    render(<SafetyAnonymityBadge masked />);

    expect(screen.getByText("Masked")).toBeInTheDocument();
    expect(screen.getByLabelText("Reporter identity masked")).toBeInTheDocument();
  });

  it("shows the visible state when identity is available to the viewer", () => {
    render(<SafetyAnonymityBadge masked={false} />);

    expect(screen.getByText("Visible")).toBeInTheDocument();
    expect(screen.getByLabelText("Reporter identity visible")).toBeInTheDocument();
  });
});
