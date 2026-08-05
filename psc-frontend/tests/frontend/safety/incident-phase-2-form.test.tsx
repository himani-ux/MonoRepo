import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SafetyIncidentPhase2Form } from "../../../src/components/safety/incident/phase2-form";

describe("SafetyIncidentPhase2Form", () => {
  it("renders the Phase 2 heading and keeps submit disabled until gate fields are complete", () => {
    render(<SafetyIncidentPhase2Form incidentId="42" />);

    expect(
      screen.getByRole("heading", { name: "Tell Office" }),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Submit" })).toBeDisabled();
  });

  it("enables submit when risk and office communication are present", () => {
    render(<SafetyIncidentPhase2Form incidentId="42" />);

    fireEvent.change(screen.getByLabelText("Risk level"), {
      target: { value: "YELLOW" },
    });
    fireEvent.change(screen.getByLabelText("Was office informed?"), {
      target: { value: "NO" },
    });

    expect(screen.getByRole("button", { name: "Submit" })).toBeEnabled();
  });

  it("shows the external expert prompt panel for RED incidents", () => {
    const onSubmitPhase = vi.fn();

    render(
      <SafetyIncidentPhase2Form incidentId="42" onSubmitPhase={onSubmitPhase} />,
    );

    fireEvent.change(screen.getByLabelText("Risk level"), {
      target: { value: "RED" },
    });

    expect(
      screen.getByRole("heading", { name: "Get outside expert help" }),
    ).toBeInTheDocument();
  });

  it("does not offer WhatsApp as an office communication method", () => {
    render(
      <SafetyIncidentPhase2Form
        incidentId="42"
        initialValues={{ office_notified: true }}
      />,
    );

    expect(screen.getByLabelText("How was office informed?")).toHaveTextContent("On call");
    expect(screen.getByLabelText("How was office informed?")).toHaveTextContent("On email");
    expect(screen.getByLabelText("How was office informed?")).not.toHaveTextContent("WhatsApp");
  });
});
