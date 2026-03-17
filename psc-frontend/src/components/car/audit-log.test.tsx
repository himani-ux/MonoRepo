/**
 * Tests for FEAT-HIST-002: Full Audit Log (CAR detail audit component)
 *
 * PRD Reference: Docs/PRD.md Section 2.9 - FEAT-HIST-002
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AuditLog } from './audit-log';

function buildEntry(overrides: Record<string, unknown> = {}) {
  return {
    id: 10,
    entity_type: 'CAR',
    entity_id: 3001,
    action: 'UPDATE',
    field_name: 'target_date',
    old_value: '2026-02-01',
    new_value: '2026-02-10',
    performed_by: 'office01',
    performed_by_role: 'OFFICE_PIC',
    performed_at: '2026-02-02T10:00:00Z',
    is_office_edit_assist: false,
    ...overrides,
  } as any;
}

describe('AuditLog', () => {
  it('test_feat_hist_002_hidden_when_entries_empty', () => {
    const { container } = render(<AuditLog entries={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('test_feat_hist_002_expands_and_renders_update_rows_with_old_and_new_values', () => {
    render(<AuditLog entries={[buildEntry()]} />);

    fireEvent.click(screen.getByRole('button', { name: /audit log \(1\)/i }));
    expect(screen.getByText('Field changed: target_date')).toBeInTheDocument();
    expect(screen.getByText(/Old:/)).toBeInTheDocument();
    expect(screen.getByText(/New:/)).toBeInTheDocument();
    expect(screen.getByText(/By: OFFICE_PIC/)).toBeInTheDocument();
  });

  it('test_feat_hist_002_empty_string_values_render_as_empty_marker_and_edit_assist_label', () => {
    render(
      <AuditLog
        entries={[
          buildEntry({
            old_value: '',
            new_value: '',
            is_office_edit_assist: true,
          }),
        ]}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /audit log \(1\)/i }));
    expect(screen.getAllByText('(empty)')).toHaveLength(2);
    expect(screen.getByText(/Edit Assist/)).toBeInTheDocument();
  });
});

