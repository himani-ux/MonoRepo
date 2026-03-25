/**
 * Tests for FEAT-CAR-011/012 corrective action item rendering rules.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-011, FEAT-CAR-012
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { CorrectiveActionItem } from './corrective-action-item';

function isoDaysOffset(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString();
}

describe('CorrectiveActionItem', () => {
  it('test_feat_car_011_overdue_open_action_highlights_due_date', () => {
    const { container } = render(
      <CorrectiveActionItem
        index={1}
        action={
          {
            id: 'a1',
            action_type: 'IMMEDIATE',
            description: 'Replace damaged hose',
            due_date: isoDaysOffset(-2),
            is_completed: false,
          } as any
        }
      />
    );

    expect(screen.getByText('Replace damaged hose')).toBeInTheDocument();
    expect(screen.getByText(/Due:/)).toBeInTheDocument();
    expect(container.firstChild).toHaveClass('border-error-300');
  });

  it('test_feat_car_012_completed_action_hides_completion_date_and_keeps_remarks', () => {
    render(
      <CorrectiveActionItem
        index={2}
        action={
          {
            id: 'a2',
            action_type: 'LONG_TERM',
            description: 'Update maintenance SOP',
            due_date: isoDaysOffset(5),
            is_completed: true,
            completed_at: isoDaysOffset(-1),
            completion_remarks: 'Completed and verified by chief engineer',
          } as any
        }
      />
    );

    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.queryByText(/Completed \d{2}/)).not.toBeInTheDocument();
    expect(
      screen.getByText('Completed and verified by chief engineer')
    ).toBeInTheDocument();
  });

  it('test_feat_car_011_shows_index_prefix_for_action_item', () => {
    render(
      <CorrectiveActionItem
        index={7}
        action={
          {
            id: 'a3',
            action_type: 'IMMEDIATE',
            description: 'Test alarm panel',
            is_completed: false,
          } as any
        }
      />
    );

    expect(screen.getByText('7.')).toBeInTheDocument();
  });
});