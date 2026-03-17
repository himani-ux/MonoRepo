/**
 * Tests for FEAT-CAR-009 CAR list card behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-009
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const carCardMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => carCardMocks.navigate,
}));

vi.mock('@/components/shared', () => ({
  StatusBadge: ({ status }: { status: string }) => <span>Status:{status}</span>,
}));

import { CARCard } from './car-card';

describe('CARCard', () => {
  beforeEach(() => {
    carCardMocks.navigate.mockReset();
  });

  it('test_feat_car_009_clicking_card_navigates_to_car_detail', () => {
    render(
      <CARCard
        id={101}
        carNumber="PSC-2026-001"
        defCode="10101"
        deficiencyDescription="Fire doors issue"
        vesselName="MV Example"
        status="ALLOTTED"
        targetDate="2026-02-15"
        isOverdue={false}
        hasMissingEvidence={false}
        inspectionType="PSC"
      />
    );

    fireEvent.click(screen.getByText('PSC-2026-001'));
    expect(carCardMocks.navigate).toHaveBeenCalledWith('/cars/101');
  });

  it('test_feat_car_009_renders_defcode_status_and_target_date', () => {
    render(
      <CARCard
        id={102}
        carNumber="RS-2026-002"
        defCode="20100"
        deficiencyDescription="Navigation light"
        vesselName="MV Sample"
        status="SUBMITTED_TO_PIC"
        targetDate="2026-03-01"
        isOverdue={false}
        hasMissingEvidence={false}
        inspectionType="RS"
      />
    );

    expect(screen.getByText('[20100]')).toBeInTheDocument();
    expect(screen.getByText('Status:SUBMITTED_TO_PIC')).toBeInTheDocument();
    expect(screen.getByText(/Target:/)).toBeInTheDocument();
  });

  it('test_feat_car_009_shows_overdue_and_missing_evidence_indicators', () => {
    render(
      <CARCard
        id={103}
        carNumber="PSC-2026-003"
        defCode="30100"
        deficiencyDescription="Lifeboat drill"
        vesselName="MV Overdue"
        status="RETURNED_FOR_REWORK"
        targetDate={null}
        isOverdue
        hasMissingEvidence
        inspectionType="PSC"
      />
    );

    expect(screen.getByText('OVERDUE')).toBeInTheDocument();
    expect(screen.getByText('Missing evidence')).toBeInTheDocument();
  });

  it('test_feat_car_009_shows_pv_due_badge_when_pv_due_true', () => {
    render(
      <CARCard
        id={104}
        carNumber="PSC-2026-004"
        defCode="40100"
        deficiencyDescription="PV follow-up required"
        vesselName="MV Due"
        status="CLOSED"
        targetDate={null}
        isOverdue={false}
        hasMissingEvidence={false}
        pvDue
        inspectionType="PSC"
      />
    );

    expect(screen.getByText('PV Due')).toBeInTheDocument();
  });
});
