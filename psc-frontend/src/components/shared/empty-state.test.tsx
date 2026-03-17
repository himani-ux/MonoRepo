/**
 * Tests for empty-state reusable views used by inspection and notification flows.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-010
 * PRD Reference: Docs/PRD.md Section 2.7 - FEAT-NOTIF-001
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import {
  EmptyState,
  EmptyStateInspections,
  EmptyStateNotifications,
} from './empty-state';

describe('EmptyState', () => {
  it('test_feat_ins_010_generic_empty_state_renders_title_description_and_action', () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        title="No records"
        description="Try changing filters."
        actionLabel="Retry"
        onAction={onAction}
      />
    );

    expect(screen.getByText('No records')).toBeInTheDocument();
    expect(screen.getByText('Try changing filters.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('test_feat_ins_010_preconfigured_inspections_empty_state_uses_expected_copy', () => {
    render(<EmptyStateInspections />);
    expect(screen.getByText('No inspections recorded yet')).toBeInTheDocument();
  });

  it('test_feat_notif_001_preconfigured_notifications_empty_state_uses_expected_copy', () => {
    render(<EmptyStateNotifications />);
    expect(screen.getByText("You're all caught up! New notifications will appear here.")).toBeInTheDocument();
  });
});

