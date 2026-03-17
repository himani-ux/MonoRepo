/**
 * Tests for FEAT-INS-004: Deficiency card rendering and navigation affordances.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-004
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import type { DeficiencyDetail } from '@/types';
import { DeficiencyCard } from './deficiency-card';

const buildDeficiency = (
  overrides: Partial<DeficiencyDetail> = {}
): DeficiencyDetail => ({
  id: 77,
  def_code: '10101',
  def_code_description: 'Life-saving appliances',
  description: 'Lifeboat launching arrangement not operational.',
  action_code: '30',
  action_code_description: 'To be rectified',
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
    id: 900,
    car_number: 'CAR-2026-0900',
    status: 'SUBMITTED_TO_PIC',
  },
  created_at: '2026-02-08T00:00:00Z',
  updated_at: '2026-02-08T00:00:00Z',
  ...overrides,
});

describe('DeficiencyCard', () => {
  it('test_feat_ins_004_renders_def_code_description_car_number_and_link', () => {
    const deficiency = buildDeficiency();

    render(
      <MemoryRouter>
        <DeficiencyCard deficiency={deficiency} />
      </MemoryRouter>
    );

    expect(screen.getByText('[10101]')).toBeInTheDocument();
    expect(screen.getByText('Life-saving appliances')).toBeInTheDocument();
    expect(screen.getByText('CAR: CAR-2026-0900')).toBeInTheDocument();

    const viewLink = screen.getByRole('link', { name: 'View CAR' });
    expect(viewLink).toHaveAttribute('href', '/cars/900');
  });

  it('test_feat_ins_004_card_click_handler_fires_when_user_clicks_card_body', () => {
    const onClick = vi.fn();

    render(
      <MemoryRouter>
        <DeficiencyCard deficiency={buildDeficiency()} onClick={onClick} />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText('CAR: CAR-2026-0900'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('test_feat_ins_004_view_car_link_stops_propagation_and_does_not_trigger_card_click', () => {
    const onClick = vi.fn();

    render(
      <MemoryRouter>
        <DeficiencyCard deficiency={buildDeficiency()} onClick={onClick} />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('link', { name: 'View CAR' }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('test_feat_ins_004_shows_target_row_and_cleared_badge_when_deficiency_is_cleared', () => {
    render(
      <MemoryRouter>
        <DeficiencyCard
          deficiency={buildDeficiency({
            is_cleared: true,
            target_date: '2026-02-20T12:00:00Z',
          })}
        />
      </MemoryRouter>
    );

    expect(screen.getByText(/Target:/)).toBeInTheDocument();
    expect(screen.getByText('Cleared')).toBeInTheDocument();
  });
});
