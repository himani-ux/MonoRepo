/**
 * Tests for FEAT-INS-010 and FEAT-INS-011: InspectionCard behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-010, FEAT-INS-011
 * Flow Reference: Docs/APP_FLOW.md Section 2.2 (Inspection List)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const inspectionCardMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => inspectionCardMocks.navigate,
}));

vi.mock('@/components/shared', () => ({
  StatusBadge: ({ status }: { status: string }) => (
    <span data-testid="status-badge">{status}</span>
  ),
}));

import { InspectionCard } from './inspection-card';

describe('InspectionCard', () => {
  beforeEach(() => {
    inspectionCardMocks.navigate.mockReset();
  });

  it('test_feat_ins_010_happy_path_renders_psc_type_location_mou_and_deficiency_counts', () => {
    render(
      <InspectionCard
        id={42}
        vesselName="MV Atlas"
        inspectionType="PSC"
        pscSubtype="INITIAL"
        inspectionDate="2026-02-08"
        port="Singapore"
        portState="SG"
        mouCode="TOKYO"
        isDetention={false}
        status="SUBMITTED"
        deficiencyCount={3}
        openDeficiencyCount={1}
      />
    );

    expect(screen.getByText('MV Atlas')).toBeInTheDocument();
    expect(screen.getAllByText('PSC - Initial').length).toBeGreaterThan(0);
    expect(screen.getByText('Singapore, SG')).toBeInTheDocument();
    expect(screen.getByText('TOKYO MOU')).toBeInTheDocument();
    expect(screen.getByText('Deficiencies:')).toBeInTheDocument();
    expect(screen.getByText('3 (1 open)')).toBeInTheDocument();
    expect(screen.getByTestId('status-badge')).toHaveTextContent('SUBMITTED');
  });

  it('test_feat_ins_011_click_navigates_to_detail_route', () => {
    render(
      <InspectionCard
        id={77}
        vesselName="MV Orion"
        inspectionType="RS"
        pscSubtype={null}
        inspectionDate="2026-02-07"
        port="Rotterdam"
        portState="NL"
        mouCode={null}
        isDetention={false}
        status="DRAFT"
        deficiencyCount={0}
      />
    );

    fireEvent.click(screen.getByText('MV Orion'));
    expect(inspectionCardMocks.navigate).toHaveBeenCalledTimes(1);
    expect(inspectionCardMocks.navigate).toHaveBeenCalledWith('/inspections/77');
  });

  it('test_feat_ins_010_detention_state_highlights_card_and_shows_detention_label', () => {
    const { container } = render(
      <InspectionCard
        id={88}
        vesselName="MV Delta"
        inspectionType="AUDIT"
        pscSubtype={null}
        inspectionDate="2026-02-06"
        port="Busan"
        portState="KR"
        mouCode={null}
        isDetention
        status="PIC_REVIEWED"
        deficiencyCount={2}
      />
    );

    expect(screen.getByText('Detention')).toBeInTheDocument();
    expect(container.firstChild).toHaveClass('border-l-4');
    expect(container.firstChild).toHaveClass('border-l-error-500');
  });
});
