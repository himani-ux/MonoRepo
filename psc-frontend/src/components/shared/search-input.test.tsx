/**
 * Tests for FEAT-INS-010/FEAT-CAR-009 search filter input behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-010
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-009
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SearchInput } from './search-input';

describe('SearchInput', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('test_feat_ins_010_debounce_calls_onchange_after_delay_and_immediate_on_each_keypress', () => {
    const onChange = vi.fn();
    const onChangeImmediate = vi.fn();

    render(
      <SearchInput
        onChange={onChange}
        onChangeImmediate={onChangeImmediate}
        debounceMs={300}
      />
    );

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'p' } });
    fireEvent.change(input, { target: { value: 'ps' } });
    fireEvent.change(input, { target: { value: 'psc' } });

    expect(onChangeImmediate).toHaveBeenCalledTimes(3);
    expect(onChange).not.toHaveBeenCalled();

    vi.advanceTimersByTime(299);
    expect(onChange).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith('psc');
  });

  it('test_feat_ins_010_clear_button_resets_value_and_cancels_pending_debounce', () => {
    const onChange = vi.fn();
    const onChangeImmediate = vi.fn();

    render(
      <SearchInput
        onChange={onChange}
        onChangeImmediate={onChangeImmediate}
        debounceMs={300}
      />
    );

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'rotterdam' } });
    fireEvent.click(screen.getByRole('button', { name: /clear search/i }));

    expect(onChangeImmediate).toHaveBeenLastCalledWith('');
    expect(onChange).toHaveBeenCalledWith('');

    vi.advanceTimersByTime(300);
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it('test_feat_car_009_external_value_updates_internal_input_state', () => {
    const { rerender } = render(<SearchInput value="initial" />);
    expect(screen.getByRole('textbox')).toHaveValue('initial');

    rerender(<SearchInput value="updated from parent" />);
    expect(screen.getByRole('textbox')).toHaveValue('updated from parent');
  });

  it('test_feat_car_009_loading_state_shows_spinner_and_hides_clear_button', () => {
    render(<SearchInput value="abc" isLoading />);

    expect(screen.queryByRole('button', { name: /clear search/i })).not.toBeInTheDocument();
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).not.toBeNull();
  });
});

