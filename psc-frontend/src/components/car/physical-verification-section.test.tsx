/**
 * Tests for FEAT-PV-001 and FEAT-PV-002 physical verification section behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.4 - FEAT-PV-001, FEAT-PV-002
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PhysicalVerificationSection } from './physical-verification-section';

function buildPV(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    car_id: 3001,
    status: 'OPEN',
    status_display: 'Open',
    scheduled_date: '2026-02-12',
    visit_date: null,
    visit_port: 'Singapore',
    verifier_user_id: 'EMP001',
    verifier_crew_id: null,
    comments: null,
    created_by: 'office01',
    created_date: '2026-02-10T08:00:00Z',
    closed_by: null,
    closed_at: null,
    ...overrides,
  } as any;
}

describe('PhysicalVerificationSection', () => {
  it('test_feat_pv_001_hidden_when_car_not_closed_and_no_verification_exists', () => {
    const { container } = render(
      <PhysicalVerificationSection
        physicalVerification={null}
        isDPAClosed={false}
        canCreatePV={false}
        canClosePV={false}
      />
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('test_feat_pv_001_no_existing_verification_shows_schedule_action_when_allowed', () => {
    const onCreatePV = vi.fn();

    render(
      <PhysicalVerificationSection
        physicalVerification={null}
        isDPAClosed
        canCreatePV
        canClosePV={false}
        onCreatePV={onCreatePV}
      />
    );

    expect(screen.getByText('No physical verification scheduled for this CAR.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /schedule verification/i }));
    expect(onCreatePV).toHaveBeenCalledTimes(1);
  });

  it('test_feat_pv_002_open_verification_shows_details_and_close_action_when_permitted', () => {
    const onClosePV = vi.fn();

    render(
      <PhysicalVerificationSection
        physicalVerification={buildPV()}
        isDPAClosed
        canCreatePV={false}
        canClosePV
        onClosePV={onClosePV}
      />
    );

    expect(screen.getByText('Physical Verification')).toBeInTheDocument();
    expect(screen.getByText('OPEN')).toBeInTheDocument();
    expect(screen.getByText(/Scheduled:/)).toBeInTheDocument();
    expect(screen.getByText('Singapore')).toBeInTheDocument();
    expect(screen.getByText(/Verifier: EMP001/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /close verification/i }));
    expect(onClosePV).toHaveBeenCalledTimes(1);
  });

  it('test_feat_pv_002_closed_verification_shows_closed_state_and_hides_close_action', () => {
    render(
      <PhysicalVerificationSection
        physicalVerification={buildPV({
          status: 'CLOSED',
          visit_date: '2026-02-14',
          comments: 'Verification completed successfully.',
          closed_at: '2026-02-14T12:00:00Z',
        })}
        isDPAClosed
        canCreatePV={false}
        canClosePV
      />
    );

    expect(screen.getByText('CLOSED')).toBeInTheDocument();
    expect(screen.getByText('Comments:')).toBeInTheDocument();
    expect(screen.getByText('Verification completed successfully.')).toBeInTheDocument();
    expect(screen.getByText(/Closed on/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /close verification/i })).not.toBeInTheDocument();
  });
});

