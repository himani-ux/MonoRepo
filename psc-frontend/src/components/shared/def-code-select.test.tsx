/**
 * Tests for FEAT-INS-003 DefCode selection behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-003
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const defCodeSelectMocks = vi.hoisted(() => ({
  usePSCDefCodes: vi.fn(),
}));

vi.mock('@/hooks/use-masters', () => ({
  usePSCDefCodes: (filters: unknown) => defCodeSelectMocks.usePSCDefCodes(filters),
}));

import { DefCodeSelect, DefCodeDisplay } from './def-code-select';

const codes = [
  {
    def_code: '10101',
    def_name: 'Fire doors',
    category_name: 'Safety',
  },
  {
    def_code: '10102',
    def_name: 'Fire dampers',
    category_name: 'Safety',
  },
] as any[];

describe('DefCodeSelect', () => {
  beforeEach(() => {
    defCodeSelectMocks.usePSCDefCodes.mockReset();
    defCodeSelectMocks.usePSCDefCodes.mockReturnValue({
      data: codes,
      isLoading: false,
    });
  });

  it('test_feat_ins_003_renders_placeholder_when_no_value_selected', () => {
    render(<DefCodeSelect />);
    expect(screen.getByRole('combobox')).toHaveTextContent('Select deficiency code');
  });

  it('test_feat_ins_003_selecting_option_calls_onchange_with_code_and_object', () => {
    const onChange = vi.fn();
    render(<DefCodeSelect onChange={onChange} />);

    fireEvent.click(screen.getByRole('combobox'));
    fireEvent.click(screen.getByRole('option', { name: /10101/i }));

    expect(onChange).toHaveBeenCalledWith('10101', expect.objectContaining({ def_code: '10101' }));
  });

  it('test_feat_ins_003_clear_selection_calls_onchange_with_empty_value', () => {
    const onChange = vi.fn();
    render(<DefCodeSelect value="10101" onChange={onChange} />);

    fireEvent.click(screen.getByRole('combobox'));
    fireEvent.click(screen.getByRole('button', { name: 'Clear selection' }));

    expect(onChange).toHaveBeenCalledWith('', null);
  });
});

describe('DefCodeDisplay', () => {
  it('test_feat_ins_003_displays_defcode_and_name', () => {
    render(<DefCodeDisplay code="10101" name="Fire doors" />);
    expect(screen.getByText('10101')).toBeInTheDocument();
    expect(screen.getByText('Fire doors')).toBeInTheDocument();
  });
});

