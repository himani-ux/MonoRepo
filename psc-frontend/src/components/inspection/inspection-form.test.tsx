/**
 * Tests for FEAT-INS-001: Create Inspection (InspectionForm component behavior)
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-001
 * Validation Reference: Docs/VALIDATION_RULES.md Section 2.1
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const inspectionFormMocks = vi.hoisted(() => ({
  onSubmit: vi.fn(),
  onCancel: vi.fn(),
  useMOUCodes: vi.fn(),
}));

vi.mock('@/hooks/use-masters', () => ({
  useMOUCodes: () => inspectionFormMocks.useMOUCodes(),
}));

vi.mock('@/components/shared', async () => {
  return {
    DatePicker: ({
      id,
      value,
      onChange,
      disabled,
    }: {
      id?: string;
      value?: string;
      onChange?: (value: string) => void;
      disabled?: boolean;
    }) => (
      <input
        id={id}
        type="date"
        value={value || ''}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
      />
    ),
    FileUpload: ({
      onChange,
      errorMessage,
      disabled,
    }: {
      onChange?: (file: File | null) => void;
      errorMessage?: string;
      disabled?: boolean;
    }) => (
      <div>
        <label htmlFor="test-file-upload">Upload file</label>
        <input
          id="test-file-upload"
          type="file"
          disabled={disabled}
          onChange={(e) => onChange?.(e.target.files?.[0] ?? null)}
        />
        {errorMessage ? <p>{errorMessage}</p> : null}
      </div>
    ),
  };
});

import { InspectionForm } from './inspection-form';

if (!globalThis.ResizeObserver) {
  vi.stubGlobal(
    'ResizeObserver',
    class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  );
}

function baseInitialValues(overrides: Record<string, unknown> = {}) {
  return {
    inspection_type: 'RS',
    psc_subtype: null,
    inspection_date: '2026-02-01',
    port: 'Singapore',
    port_state: 'SG',
    mou_code: null,
    authority: '',
    inspector_name: null,
    report_reference: '',
    is_detention: false,
    def_reported: 'NO',
    detention_reason: null,
    ...overrides,
  } as any;
}

describe('InspectionForm', () => {
  beforeEach(() => {
    inspectionFormMocks.onSubmit.mockReset();
    inspectionFormMocks.onCancel.mockReset();
    inspectionFormMocks.useMOUCodes.mockReset();
    inspectionFormMocks.useMOUCodes.mockReturnValue({
      data: [
        { mou_code: 'TOKYO', mou_name: 'Tokyo MOU' },
        { mou_code: 'PARIS', mou_name: 'Paris MOU' },
      ],
      isLoading: false,
    });
  });

  it('test_feat_ins_001_conditional_psc_fields_visible_for_psc_type', () => {
    render(
      <InspectionForm
        onSubmit={inspectionFormMocks.onSubmit}
        onCancel={inspectionFormMocks.onCancel}
        initialValues={baseInitialValues({
          inspection_type: 'PSC',
          psc_subtype: 'INITIAL',
          mou_code: 'TOKYO',
        })}
      />
    );

    expect(screen.getByText('PSC Subtype')).toBeInTheDocument();
    expect(screen.getByText('MOU')).toBeInTheDocument();
  });

  it('test_feat_ins_001_conditional_psc_fields_hidden_for_non_psc_type', () => {
    render(
      <InspectionForm
        onSubmit={inspectionFormMocks.onSubmit}
        onCancel={inspectionFormMocks.onCancel}
        initialValues={baseInitialValues({ inspection_type: 'RS' })}
      />
    );

    expect(screen.queryByText('PSC Subtype')).not.toBeInTheDocument();
    expect(screen.queryByText('MOU')).not.toBeInTheDocument();
  });

  it('test_feat_ins_001_happy_path_submit_calls_callback_with_valid_data_and_report_file', async () => {
    render(
      <InspectionForm
        onSubmit={inspectionFormMocks.onSubmit}
        onCancel={inspectionFormMocks.onCancel}
        initialValues={baseInitialValues()}
      />
    );

    const file = new File(['report'], 'inspection.pdf', {
      type: 'application/pdf',
    });
    fireEvent.change(screen.getByLabelText('Upload file'), {
      target: { files: [file] },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Create Draft' }));

    await waitFor(() => {
      expect(inspectionFormMocks.onSubmit).toHaveBeenCalledTimes(1);
    });
    expect(inspectionFormMocks.onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        inspection_type: 'RS',
        port: 'Singapore',
      }),
      file
    );
  });

  it('test_feat_ins_001_validation_invalid_report_file_type_shows_error_and_submits_without_file', async () => {
    render(
      <InspectionForm
        onSubmit={inspectionFormMocks.onSubmit}
        onCancel={inspectionFormMocks.onCancel}
        initialValues={baseInitialValues()}
      />
    );

    const invalidFile = new File(['bad'], 'bad.txt', { type: 'text/plain' });
    fireEvent.change(screen.getByLabelText('Upload file'), {
      target: { files: [invalidFile] },
    });

    expect(screen.getByText('Only PDF, JPG, and JPEG files are allowed')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Create Draft' }));
    await waitFor(() => {
      expect(inspectionFormMocks.onSubmit).toHaveBeenCalledTimes(1);
    });
    expect(inspectionFormMocks.onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ inspection_type: 'RS' }),
      null
    );
  });

  it('test_feat_ins_001_detention_reason_field_toggles_with_detention_checkbox', () => {
    render(
      <InspectionForm
        onSubmit={inspectionFormMocks.onSubmit}
        onCancel={inspectionFormMocks.onCancel}
        initialValues={baseInitialValues({ is_detention: false })}
      />
    );

    expect(screen.queryByLabelText('Detention Reason')).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Detention'));
    expect(screen.getByLabelText('Detention Reason')).toBeInTheDocument();
  });

  it('test_feat_ins_001_cancel_action_calls_on_cancel_callback', () => {
    render(
      <InspectionForm
        onSubmit={inspectionFormMocks.onSubmit}
        onCancel={inspectionFormMocks.onCancel}
        initialValues={baseInitialValues()}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(inspectionFormMocks.onCancel).toHaveBeenCalledTimes(1);
  });
});
