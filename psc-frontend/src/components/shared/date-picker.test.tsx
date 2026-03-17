/**
 * Tests for date picker constraints used across inspection and follow-up flows.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-001
 * PRD Reference: Docs/PRD.md Section 2.2 - FEAT-DEF-002
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DatePicker } from './date-picker';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

describe('DatePicker', () => {
  it('test_feat_ins_001_disable_future_sets_max_to_today', () => {
    render(<DatePicker disableFuture />);
    expect(screen.getByDisplayValue('').getAttribute('max')).toBe(todayIso());
  });

  it('test_feat_def_002_disable_past_sets_min_to_today', () => {
    render(<DatePicker disablePast />);
    expect(screen.getByDisplayValue('').getAttribute('min')).toBe(todayIso());
  });

  it('test_feat_ins_001_calls_onchange_with_iso_date_string', () => {
    const onChange = (value: string) => {
      (onChange as any).calls = ((onChange as any).calls || []).concat(value);
    };
    render(<DatePicker onChange={onChange} />);

    fireEvent.change(screen.getByDisplayValue(''), {
      target: { value: '2026-02-08' },
    });

    expect((onChange as any).calls).toEqual(['2026-02-08']);
  });

  it('test_feat_ins_001_respects_explicit_min_and_max_when_future_past_flags_not_used', () => {
    render(<DatePicker minDate="2026-01-01" maxDate="2026-12-31" />);
    const input = screen.getByDisplayValue('');

    expect(input.getAttribute('min')).toBe('2026-01-01');
    expect(input.getAttribute('max')).toBe('2026-12-31');
  });
});

