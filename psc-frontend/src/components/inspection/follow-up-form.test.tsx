/**
 * Tests for FEAT-DEF-002 follow-up form behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.2 - FEAT-DEF-002
 * Flow Reference: Docs/APP_FLOW.md Section 2.2 (Register Follow-up)
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { forwardRef } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const followUpFormMocks = vi.hoisted(() => ({
  usePSCActionCodes: vi.fn(),
}));

vi.mock('@/hooks/use-masters', () => ({
  usePSCActionCodes: () => followUpFormMocks.usePSCActionCodes(),
}));

vi.mock('@/components/shared', () => ({
  DatePicker: ({
    id,
    value,
    onChange,
  }: {
    id?: string;
    value?: string;
    onChange?: (value: string) => void;
  }) => (
    <input
      id={id}
      type="date"
      value={value || ''}
      onChange={(e) => onChange?.(e.target.value)}
    />
  ),
}));

vi.mock('@/components/ui', () => ({
  Button: ({
    children,
    onClick,
    ...rest
  }: {
    children: React.ReactNode;
    onClick?: () => void;
  }) => (
    <button onClick={onClick} {...rest}>
      {children}
    </button>
  ),
  Input: (() => {
    const MockInput = forwardRef<HTMLInputElement, {
      id?: string;
      value?: string;
      onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
    }>(({
      id,
      value,
      onChange,
      ...rest
    }, ref) => <input ref={ref} id={id} value={value} onChange={onChange} {...rest} />);
    MockInput.displayName = 'Input';
    return MockInput;
  })(),
  Label: ({
    children,
    htmlFor,
  }: {
    children: React.ReactNode;
    htmlFor?: string;
  }) => <label htmlFor={htmlFor}>{children}</label>,
  Checkbox: ({
    id,
    checked,
    onCheckedChange,
  }: {
    id?: string;
    checked?: boolean;
    onCheckedChange?: (checked: boolean) => void;
  }) => (
    <input
      id={id}
      type="checkbox"
      checked={!!checked}
      onChange={(e) => onCheckedChange?.(e.target.checked)}
    />
  ),
  Select: ({
    value,
    onValueChange,
    children,
  }: {
    value?: string;
    onValueChange?: (value: string) => void;
    children: React.ReactNode;
  }) => (
    <select
      data-testid="action-code-select"
      value={value}
      onChange={(e) => onValueChange?.(e.target.value)}
    >
      {children}
    </select>
  ),
  SelectContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectItem: ({ value, children }: { value: string; children: React.ReactNode }) => (
    <option value={value}>{children}</option>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectValue: () => null,
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import { FollowUpForm } from './follow-up-form';

function buildParentInspection(overrides: Record<string, unknown> = {}) {
  return {
    id: 100,
    inspection_type: 'PSC',
    psc_subtype: 'INITIAL',
    inspection_date: '2026-02-01',
    port: 'Singapore',
    port_state: 'Singapore',
    authority: 'MPA',
    deficiencies: [
      {
        id: 1,
        def_code: '10101',
        def_code_description: 'Fire doors',
        action_code: '30',
        action_code_description: 'To be rectified',
        is_cleared: false,
      },
      {
        id: 2,
        def_code: '10102',
        def_code_description: 'Fire dampers',
        action_code: '10',
        action_code_description: 'Rectified',
        is_cleared: true,
      },
    ],
    ...overrides,
  } as any;
}

describe('FollowUpForm', () => {
  beforeEach(() => {
    followUpFormMocks.usePSCActionCodes.mockReset();
    followUpFormMocks.usePSCActionCodes.mockReturnValue({
      data: [
        { action_code: '10', description: 'Rectified' },
        { action_code: '17', description: 'To be rectified at next port' },
      ],
      isLoading: false,
    });
  });

  it('test_feat_def_002_shows_only_open_deficiencies_for_selection', () => {
    render(
      <FollowUpForm
        parentInspection={buildParentInspection()}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByText('Open Deficiencies')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('10101')).toBeInTheDocument();
    expect(screen.queryByText('10102')).not.toBeInTheDocument();
  });

  it('test_feat_def_002_submit_includes_selected_deficiency_updates_with_changed_action_code', async () => {
    const onSubmit = vi.fn();
    render(
      <FollowUpForm
        parentInspection={buildParentInspection()}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.change(screen.getByTestId('action-code-select'), {
      target: { value: '17' },
    });
    fireEvent.change(screen.getByLabelText(/Follow-up Date/i), {
      target: { value: '2026-02-08' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Register Follow-up' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          deficiency_updates: [{ deficiency_id: 1, action_code_id: 17 }],
          port_place: 'Singapore',
        })
      );
    });
  });

  it('test_feat_def_002_cancel_calls_oncancel_handler', () => {
    const onCancel = vi.fn();
    render(
      <FollowUpForm
        parentInspection={buildParentInspection()}
        onSubmit={vi.fn()}
        onCancel={onCancel}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('test_feat_def_002_when_no_open_deficiencies_shows_empty_message', () => {
    render(
      <FollowUpForm
        parentInspection={buildParentInspection({
          deficiencies: [
            {
              id: 2,
              def_code: '10102',
              def_code_description: 'Fire dampers',
              action_code: '10',
              action_code_description: 'Rectified',
              is_cleared: true,
            },
          ],
        })}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByText('No open deficiencies to update.')).toBeInTheDocument();
  });
});
