/**
 * Tests for FEAT-INS-010: Inspection filter controls behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-010
 * Flow Reference: Docs/APP_FLOW.md Section 2.2 (Inspection List)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import type { InspectionFilters as FilterType } from '@/types';

vi.mock('@/components/ui', () => ({
  Select: ({
    value,
    onValueChange,
    children,
  }: {
    value: string;
    onValueChange?: (value: string) => void;
    children?: ReactNode;
  }) => (
    <select
      value={value}
      onChange={(event) => onValueChange?.(event.target.value)}
    >
      {children}
    </select>
  ),
  SelectTrigger: ({ children }: { children?: ReactNode }) => <>{children}</>,
  SelectValue: () => null,
  SelectContent: ({ children }: { children?: ReactNode }) => <>{children}</>,
  SelectItem: ({
    value,
    children,
  }: {
    value: string;
    children?: ReactNode;
  }) => <option value={value}>{children}</option>,
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

import { InspectionFilters } from './inspection-filters';

describe('InspectionFilters', () => {
  it('test_feat_ins_010_type_change_sets_inspection_type_and_preserves_other_fields', () => {
    const onFiltersChange = vi.fn();
    const filters: FilterType = { status: 'SUBMITTED', search: 'atlas' };

    render(<InspectionFilters filters={filters} onFiltersChange={onFiltersChange} />);

    fireEvent.change(screen.getAllByRole('combobox')[0], {
      target: { value: 'PSC' },
    });

    expect(onFiltersChange).toHaveBeenCalledWith({
      status: 'SUBMITTED',
      search: 'atlas',
      inspection_type: 'PSC',
    });
  });

  it('test_feat_ins_010_status_change_sets_status_filter_and_selecting_all_clears_it', () => {
    const onFiltersChange = vi.fn();
    const filters: FilterType = { inspection_type: 'RS', search: 'rotterdam' };

    render(<InspectionFilters filters={filters} onFiltersChange={onFiltersChange} />);

    fireEvent.change(screen.getAllByRole('combobox')[1], {
      target: { value: 'CLOSED' },
    });
    fireEvent.change(screen.getAllByRole('combobox')[1], {
      target: { value: 'all' },
    });

    expect(onFiltersChange).toHaveBeenNthCalledWith(1, {
      inspection_type: 'RS',
      search: 'rotterdam',
      status: 'CLOSED',
    });
    expect(onFiltersChange).toHaveBeenNthCalledWith(2, {
      inspection_type: 'RS',
      search: 'rotterdam',
      status: undefined,
    });
  });

  it('test_feat_ins_010_search_change_maps_empty_value_to_undefined', () => {
    const onFiltersChange = vi.fn();
    const filters: FilterType = { inspection_type: 'PSC', search: 'mv atlas' };

    render(<InspectionFilters filters={filters} onFiltersChange={onFiltersChange} />);

    fireEvent.change(screen.getByLabelText('Search'), { target: { value: '' } });
    expect(onFiltersChange).toHaveBeenCalledWith({
      inspection_type: 'PSC',
      search: undefined,
    });
  });

  it('test_feat_ins_010_clear_button_visible_for_active_filters_and_resets_to_empty_object', () => {
    const onFiltersChange = vi.fn();

    render(
      <InspectionFilters
        filters={{ is_detention: false }}
        onFiltersChange={onFiltersChange}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /clear/i }));
    expect(onFiltersChange).toHaveBeenCalledWith({});
  });

  it('test_feat_ins_010_clear_button_hidden_when_no_active_filters', () => {
    render(<InspectionFilters filters={{}} onFiltersChange={vi.fn()} />);

    expect(
      screen.queryByRole('button', { name: /clear/i })
    ).not.toBeInTheDocument();
  });

  it('shows_detention_toggle_as_active_filter_control', () => {
    const onFiltersChange = vi.fn();

    render(<InspectionFilters filters={{ status: 'OPEN' as any }} onFiltersChange={onFiltersChange} />);

    fireEvent.click(screen.getByRole('button', { name: 'Detentions' }));

    expect(onFiltersChange).toHaveBeenCalledWith({
      status: 'OPEN',
      is_detention: true,
    });
  });

  it('shows_active_chip_for_detention_state_from_navigation_filters', () => {
    render(
      <InspectionFilters
        filters={{ is_detention: true, date_from: '2023-02-12' }}
        onFiltersChange={vi.fn()}
      />
    );

    expect(screen.getByText('Detention active')).toBeInTheDocument();
    expect(screen.getByText('From 2023-02-12')).toBeInTheDocument();
  });
});
