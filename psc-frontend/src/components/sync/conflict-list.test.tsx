/**
 * Tests for FEAT-SYNC-004 and FEAT-SYNC-005: Conflict list behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-004, FEAT-SYNC-005
 * Flow Reference: Docs/APP_FLOW.md Section 2.5 (Sync Status)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ConflictList } from './conflict-list';

function buildConflict(overrides: Record<string, unknown> = {}) {
  return {
    id: 'conflict-1',
    vessel_id: 101,
    entity_type: 'INSPECTION',
    entity_id: '9001',
    server_data: { status: 'SUBMITTED' },
    vessel_data: { status: 'DRAFT' },
    conflicting_fields: ['status'],
    status: 'OPEN',
    resolution: null,
    resolved_by: null,
    resolved_at: null,
    resolution_notes: null,
    created_date: '2026-02-08T08:00:00Z',
    ...overrides,
  } as any;
}

describe('ConflictList', () => {
  it('test_feat_sync_004_hidden_when_no_conflicts_returns_null', () => {
    const { container } = render(
      <ConflictList conflicts={[]} canResolve={false} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('test_feat_sync_004_happy_path_renders_count_entity_label_and_fields', () => {
    render(
      <ConflictList
        conflicts={[
          buildConflict({
            entity_type: 'DEFICIENCY',
            entity_id: 'D-100',
            conflicting_fields: ['action_code', 'target_date'],
          }),
        ]}
        canResolve={false}
      />
    );

    expect(screen.getByText('Conflicts')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('Deficiency #D-100')).toBeInTheDocument();
    expect(
      screen.getByText('2 conflicting fields: action_code, target_date')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Waiting for office to resolve')
    ).toBeInTheDocument();
  });

  it('test_feat_sync_005_resolve_button_visible_for_office_and_calls_handler', () => {
    const onResolve = vi.fn();
    const conflict = buildConflict({
      entity_type: 'CAR',
      entity_id: 'CAR-42',
      conflicting_fields: ['root_cause_summary'],
    });

    render(
      <ConflictList conflicts={[conflict]} canResolve onResolve={onResolve} />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Resolve' }));
    expect(onResolve).toHaveBeenCalledTimes(1);
    expect(onResolve).toHaveBeenCalledWith(conflict);
    expect(
      screen.queryByText('Waiting for office to resolve')
    ).not.toBeInTheDocument();
  });
});
