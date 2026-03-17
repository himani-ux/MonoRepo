/**
 * Tests for FEAT-INS-004: Deficiency list rendering and interactions.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-004
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { DeficiencyDetail } from '@/types';

vi.mock('@/hooks/use-deficiencies', () => ({
  useBulkSubmitDeficiencies: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

vi.mock('./deficiency-card', () => ({
  DeficiencyCard: ({
    deficiency,
    onClick,
  }: {
    deficiency: DeficiencyDetail;
    onClick?: () => void;
  }) => (
    <button
      type="button"
      data-testid={`deficiency-card-${deficiency.id}`}
      onClick={onClick}
    >
      {deficiency.def_code}
    </button>
  ),
}));

import { DeficiencyList } from './deficiency-list';

const buildDeficiency = (
  overrides: Partial<DeficiencyDetail> = {}
): DeficiencyDetail => ({
  id: 1,
  def_code: '10101',
  def_code_description: 'Fire safety',
  description: 'Fire door damaged',
  action_code: null,
  action_code_description: null,
  target_date: null,
  is_cleared: false,
  assigned_crew_id: null,
  assigned_crew_name: null,
  def_status: 'IN_PROGRESS',
  reviewer_crew_id: null,
  owner_rank: null,
  owner_name: null,
  reviewer_rank: null,
  reviewer_name: null,
  car: {
    id: 10,
    car_number: 'CAR-0010',
    status: 'SUBMITTED_TO_PIC',
  },
  created_at: '2026-02-08T00:00:00Z',
  updated_at: '2026-02-08T00:00:00Z',
  ...overrides,
});

describe('DeficiencyList', () => {
  it('test_feat_ins_004_empty_state_shows_add_deficiency_action_when_handler_provided', () => {
    const onAddDeficiency = vi.fn();

    render(<DeficiencyList deficiencies={[]} onAddDeficiency={onAddDeficiency} />);

    expect(screen.getByText('DEFICIENCIES (0)')).toBeInTheDocument();
    expect(screen.getByText('No deficiencies')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Add Deficiency' }));
    expect(onAddDeficiency).toHaveBeenCalledTimes(1);
  });

  it('test_feat_ins_004_list_header_shows_total_and_open_counts', () => {
    render(
      <DeficiencyList
        deficiencies={[
          buildDeficiency({ id: 1, is_cleared: false }),
          buildDeficiency({ id: 2, is_cleared: true }),
        ]}
      />
    );

    expect(screen.getByText('DEFICIENCIES (2)')).toBeInTheDocument();
    expect(screen.getByText('1 open')).toBeInTheDocument();
  });

  it('test_feat_ins_004_clicking_card_calls_onDeficiencyClick_with_selected_item', () => {
    const first = buildDeficiency({ id: 1, def_code: '10101' });
    const second = buildDeficiency({ id: 2, def_code: '20202' });
    const onDeficiencyClick = vi.fn();

    render(
      <DeficiencyList
        deficiencies={[first, second]}
        onDeficiencyClick={onDeficiencyClick}
      />
    );

    fireEvent.click(screen.getByTestId('deficiency-card-2'));
    expect(onDeficiencyClick).toHaveBeenCalledWith(second);
  });
});
