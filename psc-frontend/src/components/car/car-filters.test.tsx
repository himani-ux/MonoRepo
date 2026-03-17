/**
 * Tests for FEAT-CAR-010: CAR filter controls behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-010
 */

import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import type { CARFilters as FilterType } from '@/types';

vi.mock('@/components/ui', () => ({
  Select: ({
    value,
    onValueChange,
  }: {
    value: string;
    onValueChange?: (value: string) => void;
  }) => (
    <select
      aria-label="Status"
      value={value}
      onChange={(event) => onValueChange?.(event.target.value)}
    >
      <option value="all">All Statuses</option>
      <option value="DRAFT">Draft</option>
      <option value="SUBMITTED">Submitted</option>
      <option value="PIC_ACCEPTED">PIC Accepted</option>
      <option value="REWORK_REQUESTED">Rework Requested</option>
      <option value="DPA_CLOSED">Closed</option>
    </select>
  ),
  SelectTrigger: () => null,
  SelectValue: () => null,
  SelectContent: () => null,
  SelectItem: () => null,
  Button: ({
    children,
    onClick,
  }: {
    children: ReactNode;
    onClick?: () => void;
  }) => (
    <button type="button" onClick={onClick}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/shared', () => ({
  SearchInput: ({
    value,
    onChange,
    placeholder,
  }: {
    value?: string;
    onChange?: (value: string) => void;
    placeholder?: string;
  }) => (
    <input
      aria-label="Search"
      value={value ?? ''}
      placeholder={placeholder}
      onChange={(event) => onChange?.(event.target.value)}
    />
  ),
}));

import { CARFilters } from './car-filters';

describe('CARFilters', () => {
  it('test_feat_car_010_status_change_sets_status_filter_and_preserves_other_fields', () => {
    const onFiltersChange = vi.fn();
    const filters: FilterType = { search: 'atlas' };

    render(<CARFilters filters={filters} onFiltersChange={onFiltersChange} />);

    fireEvent.change(screen.getByLabelText('Status'), {
      target: { value: 'SUBMITTED_TO_PIC' },
    });

    expect(onFiltersChange).toHaveBeenCalledWith({
      search: 'atlas',
      status: 'SUBMITTED_TO_PIC',
    });
  });

  it('test_feat_car_010_selecting_all_statuses_clears_status_filter', () => {
    const onFiltersChange = vi.fn();
    const filters: FilterType = { status: 'PIC_REVIEW', search: 'mv' };

    render(<CARFilters filters={filters} onFiltersChange={onFiltersChange} />);

    fireEvent.change(screen.getByLabelText('Status'), {
      target: { value: 'all' },
    });

    expect(onFiltersChange).toHaveBeenCalledWith({
      status: undefined,
      search: 'mv',
    });
  });

  it('test_feat_car_010_search_change_updates_search_and_empty_value_maps_to_undefined', () => {
    const onFiltersChange = vi.fn();
    const filters: FilterType = { status: 'ALLOTTED', search: 'psc-2026' };

    render(<CARFilters filters={filters} onFiltersChange={onFiltersChange} />);

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: '' },
    });

    expect(onFiltersChange).toHaveBeenCalledWith({
      status: 'ALLOTTED',
      search: undefined,
    });
  });

  it('test_feat_car_010_clear_button_appears_for_active_filters_and_resets_to_empty_object', () => {
    const onFiltersChange = vi.fn();

    render(
      <CARFilters
        filters={{ has_missing_evidence: true }}
        onFiltersChange={onFiltersChange}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /clear/i }));
    expect(onFiltersChange).toHaveBeenCalledWith({});
  });

  it('test_feat_car_010_clear_button_hidden_when_no_active_filters', () => {
    render(<CARFilters filters={{}} onFiltersChange={vi.fn()} />);

    expect(
      screen.queryByRole('button', { name: /clear/i })
    ).not.toBeInTheDocument();
  });

  it('test_feat_car_010_pv_due_toggle_sets_pv_due_filter_true', () => {
    const onFiltersChange = vi.fn();

    render(<CARFilters filters={{ status: 'CLOSED' as any }} onFiltersChange={onFiltersChange} />);

    fireEvent.click(screen.getByRole('button', { name: 'PV Due' }));

    expect(onFiltersChange).toHaveBeenCalledWith({
      status: 'CLOSED',
      pv_due: true,
    });
  });

  it('shows_overdue_toggle_as_actionable_filter_control', () => {
    const onFiltersChange = vi.fn();

    render(<CARFilters filters={{ search: 'atlas' }} onFiltersChange={onFiltersChange} />);

    fireEvent.click(screen.getByRole('button', { name: 'Overdue' }));

    expect(onFiltersChange).toHaveBeenCalledWith({
      search: 'atlas',
      is_overdue: true,
    });
  });

  it('shows_active_chip_for_overdue_filter_state', () => {
    render(<CARFilters filters={{ is_overdue: true }} onFiltersChange={vi.fn()} />);

    expect(screen.getByText('Overdue active')).toBeInTheDocument();
  });
});
