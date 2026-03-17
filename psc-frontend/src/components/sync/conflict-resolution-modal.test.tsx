/**
 * Tests for FEAT-SYNC-005: Conflict resolution modal behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-005
 * Validation Reference: Docs/VALIDATION_RULES.md Section 8.5
 * Flow Reference: Docs/APP_FLOW.md Section 2.5 (Sync Status)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ConflictResolutionModal } from './conflict-resolution-modal';

function buildConflict(overrides: Record<string, unknown> = {}) {
  return {
    id: 'sync-conflict-1',
    vessel_id: 200,
    entity_type: 'CAR',
    entity_id: '3001',
    server_data: {
      status: 'SUBMITTED',
      is_detention: true,
      target_date: null,
      metadata: { source: 'office' },
    },
    vessel_data: {
      status: 'DRAFT',
      is_detention: false,
      target_date: '2026-02-14',
      metadata: { source: 'vessel' },
    },
    conflicting_fields: ['status', 'is_detention', 'target_date', 'metadata'],
    status: 'OPEN',
    resolution: null,
    resolved_by: null,
    resolved_at: null,
    resolution_notes: null,
    created_date: '2026-02-08T10:00:00Z',
    ...overrides,
  } as any;
}

describe('ConflictResolutionModal', () => {
  it('test_feat_sync_005_not_rendered_when_conflict_is_null', () => {
    render(
      <ConflictResolutionModal
        open
        onOpenChange={vi.fn()}
        conflict={null}
        onResolve={vi.fn()}
      />
    );

    expect(screen.queryByText('Resolve Conflict')).not.toBeInTheDocument();
  });

  it('test_feat_sync_005_happy_path_renders_comparison_table_and_formatted_values', () => {
    render(
      <ConflictResolutionModal
        open
        onOpenChange={vi.fn()}
        conflict={buildConflict()}
        onResolve={vi.fn()}
      />
    );

    expect(screen.getByText('Resolve Conflict')).toBeInTheDocument();
    expect(screen.getByText('CAR #3001 has conflicting changes.')).toBeInTheDocument();
    expect(
      screen.getByRole('table', { name: 'Conflicting fields comparison' })
    ).toBeInTheDocument();
    expect(screen.getByText('Is Detention')).toBeInTheDocument();
    expect(screen.getByText('Yes')).toBeInTheDocument();
    expect(screen.getByText('No')).toBeInTheDocument();
    expect(screen.getByText('(empty)')).toBeInTheDocument();
    expect(
      screen.getByText('{"source":"vessel"}')
    ).toBeInTheDocument();
  });

  it('test_feat_sync_005_apply_resolution_disabled_until_selection_then_calls_on_resolve', () => {
    const onResolve = vi.fn();

    render(
      <ConflictResolutionModal
        open
        onOpenChange={vi.fn()}
        conflict={buildConflict()}
        onResolve={onResolve}
      />
    );

    const applyButton = screen.getByRole('button', { name: 'Apply Resolution' });
    expect(applyButton).toBeDisabled();

    fireEvent.click(screen.getByRole('radio', { name: /^Keep Vessel Version/ }));
    fireEvent.change(screen.getByLabelText('Notes Optional'), {
      target: { value: 'Vessel update aligns with latest onboard evidence.' },
    });

    expect(applyButton).not.toBeDisabled();
    fireEvent.click(applyButton);

    expect(onResolve).toHaveBeenCalledTimes(1);
    expect(onResolve).toHaveBeenCalledWith(
      'sync-conflict-1',
      'KEEP_VESSEL',
      'Vessel update aligns with latest onboard evidence.'
    );
  });

  it('test_feat_sync_005_cancel_resets_local_state_and_invokes_open_change_false', () => {
    const onOpenChange = vi.fn();

    render(
      <ConflictResolutionModal
        open
        onOpenChange={onOpenChange}
        conflict={buildConflict()}
        onResolve={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('radio', { name: /^Keep Server Version/ }));
    fireEvent.change(screen.getByLabelText('Notes Optional'), {
      target: { value: 'Temporary note' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(screen.getByLabelText('Notes Optional')).toHaveValue('');
    expect(
      screen.getByRole('button', { name: 'Apply Resolution' })
    ).toBeDisabled();
  });
});
