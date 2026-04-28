/**
 * Tests for FEAT-CAR-011 action grouping and ordering in corrective action list.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-011
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('./corrective-action-item', () => ({
  CorrectiveActionItem: ({
    action,
    index,
  }: {
    action: { id: string };
    index: number;
  }) => <div>{`item:${action.id}:index:${index}`}</div>,
}));

import { CorrectiveActionList } from './corrective-action-list';

describe('CorrectiveActionList', () => {
  it('test_feat_car_011_groups_actions_into_immediate_and_long_term_sections', () => {
    render(
      <CorrectiveActionList
        actions={
          [
            { id: 'l2', action_type: 'LONG_TERM', sequence_no: 2 },
            { id: 'i1', action_type: 'IMMEDIATE', sequence_no: 1 },
            { id: 'l1', action_type: 'LONG_TERM', sequence_no: 1 },
          ] as any
        }
      />
    );

    expect(screen.getByText('IMMEDIATE (1)')).toBeInTheDocument();
    expect(screen.getByText('LONG-TERM (2)')).toBeInTheDocument();
  });

  it('test_feat_car_011_applies_sequence_sorting_and_resets_item_indexing_per_section', () => {
    render(
      <CorrectiveActionList
        actions={
          [
            { id: 'l2', action_type: 'LONG_TERM', sequence_no: 2 },
            { id: 'i2', action_type: 'IMMEDIATE', sequence_no: 2 },
            { id: 'i1', action_type: 'IMMEDIATE', sequence_no: 1 },
            { id: 'l1', action_type: 'LONG_TERM', sequence_no: 1 },
          ] as any
        }
      />
    );

    expect(screen.getByText('item:i1:index:1')).toBeInTheDocument();
    expect(screen.getByText('item:i2:index:2')).toBeInTheDocument();
    expect(screen.getByText('item:l1:index:1')).toBeInTheDocument();
    expect(screen.getByText('item:l2:index:2')).toBeInTheDocument();
  });

  it('test_feat_car_011_empty_actions_shows_placeholder_message', () => {
    render(<CorrectiveActionList actions={[]} />);
    expect(screen.getByText('No corrective actions added yet')).toBeInTheDocument();
  });
});

