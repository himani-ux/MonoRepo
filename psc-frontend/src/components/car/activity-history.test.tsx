/**
 * Tests for FEAT-HIST-001: Activity History (CAR detail timeline component)
 *
 * PRD Reference: Docs/PRD.md Section 2.9 - FEAT-HIST-001
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ActivityHistory } from './activity-history';

function buildEvent(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    entity_type: 'CAR',
    entity_id: 3001,
    event_type: 'CAR_CREATED',
    event_description: 'CAR created',
    performed_by: 'master01',
    performed_by_name: 'Master User',
    performed_at: '2026-02-01T08:00:00Z',
    metadata: {},
    ...overrides,
  } as any;
}

describe('ActivityHistory', () => {
  it('test_feat_hist_001_collapsed_by_default_and_expands_to_show_events', () => {
    render(
      <ActivityHistory
        events={[
          buildEvent(),
          buildEvent({
            id: 2,
            event_type: 'EVIDENCE_UPLOADED',
            event_description: 'Evidence uploaded',
            performed_by_name: 'Crew User',
          }),
        ]}
      />
    );

    expect(screen.getByRole('button', { name: /activity history \(2\)/i })).toBeInTheDocument();
    expect(screen.queryByText('CAR created')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /activity history \(2\)/i }));
    expect(screen.getByText('CAR created')).toBeInTheDocument();
    expect(screen.getByText('Evidence uploaded')).toBeInTheDocument();
    expect(screen.getByText(/Master User/i)).toBeInTheDocument();
    expect(screen.getByText(/Crew User/i)).toBeInTheDocument();
  });

  it('test_feat_hist_001_empty_state_shows_message_when_expanded_without_events', () => {
    render(<ActivityHistory events={[]} />);

    fireEvent.click(screen.getByRole('button', { name: /activity history \(0\)/i }));
    expect(screen.getByText('No activity recorded yet')).toBeInTheDocument();
  });
});

