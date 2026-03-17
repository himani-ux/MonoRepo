/**
 * Tests for FEAT-INS-001 and FEAT-INS-002 route behavior on Create Inspection page.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-001, FEAT-INS-002
 * Flow Reference: Docs/APP_FLOW.md Section 2.2 (Create Inspection)
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const createInspectionPageMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  useAuth: vi.fn(),
  toast: vi.fn(),
  useCreateInspection: vi.fn(),
  createMutateAsync: vi.fn(),
  uploadInspectionReport: vi.fn(),
  inspectionFormProps: null as any,
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => createInspectionPageMocks.navigate,
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => createInspectionPageMocks.useAuth(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: createInspectionPageMocks.toast }),
}));

vi.mock('@/hooks/use-inspections', () => ({
  useCreateInspection: () => createInspectionPageMocks.useCreateInspection(),
}));

vi.mock('@/lib/api/inspections', () => ({
  inspectionsApi: {
    uploadInspectionReport: (...args: unknown[]) =>
      createInspectionPageMocks.uploadInspectionReport(...args),
  },
}));

vi.mock('@/lib/api/client', () => ({
  getErrorMessage: () => 'Request failed',
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock('@/components/shared', () => ({
  ConfirmDialog: ({
    open,
    onConfirm,
  }: {
    open: boolean;
    onConfirm: () => void;
  }) => (open ? <button onClick={onConfirm}>Confirm Discard</button> : null),
}));

vi.mock('@/components/inspection/inspection-form', () => ({
  InspectionForm: (props: any) => {
    createInspectionPageMocks.inspectionFormProps = props;
    return (
      <div>
        <button
          type="button"
          onClick={() =>
            props.onSubmit(
              {
                inspection_type: 'PSC',
                psc_subtype: 'INITIAL',
                inspection_date: '2026-02-08',
                port: 'Singapore',
                port_state: 'SG',
                mou_code: 'TOKYO',
                inspector_name: 'Inspector',
                is_detention: false,
                def_reported: 'NO',
                detention_reason: null,
              },
              null
            )
          }
        >
          Trigger Submit
        </button>
        <button type="button" onClick={props.onCancel}>
          Trigger Cancel
        </button>
        <button
          type="button"
          onClick={() =>
            props.onSubmit(
              {
                inspection_type: 'PSC',
                psc_subtype: 'INITIAL',
                inspection_date: '2026-02-08',
                port: 'Singapore',
                port_state: 'SG',
                mou_code: 'TOKYO',
                inspector_name: 'Inspector',
                is_detention: false,
                def_reported: 'NO',
                detention_reason: null,
              },
              new File(['x'], 'report.pdf', { type: 'application/pdf' })
            )
          }
        >
          Trigger Submit With Report
        </button>
      </div>
    );
  },
}));

import CreateInspectionPage from './new';

describe('CreateInspectionPage', () => {
  beforeEach(() => {
    createInspectionPageMocks.navigate.mockReset();
    createInspectionPageMocks.useAuth.mockReset();
    createInspectionPageMocks.toast.mockReset();
    createInspectionPageMocks.useCreateInspection.mockReset();
    createInspectionPageMocks.createMutateAsync.mockReset();
    createInspectionPageMocks.uploadInspectionReport.mockReset();
    createInspectionPageMocks.inspectionFormProps = null;

    createInspectionPageMocks.createMutateAsync.mockResolvedValue({ id: 'ins-100' });
    createInspectionPageMocks.uploadInspectionReport.mockResolvedValue({});

    createInspectionPageMocks.useCreateInspection.mockReturnValue({
      mutateAsync: createInspectionPageMocks.createMutateAsync,
      isPending: false,
    });
    createInspectionPageMocks.useAuth.mockReturnValue({
      user: {
        user_type: 'vessel',
        role: 'VESSEL_MASTER',
        vessel_id: 'vessel-1',
      },
    });
  });

  it('test_feat_ins_001_happy_path_creates_draft_and_navigates_to_list', async () => {
    render(<CreateInspectionPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Submit' }));

    await waitFor(() => {
      expect(createInspectionPageMocks.createMutateAsync).toHaveBeenCalledWith({
        vessel_id: 'vessel-1',
        inspection_type: 'PSC',
        psc_subtype: 'INITIAL',
        inspection_date: '2026-02-08',
        port_place: 'Singapore',
        country: 'SG',
        mou_id: 'TOKYO',
        authority: undefined,
        inspector_name: 'Inspector',
        is_detention: false,
        detention_reason: '',
        def_reported: 'NO',
      });
      expect(createInspectionPageMocks.navigate).toHaveBeenCalledWith('/inspections', {
        replace: true,
      });
    });
  });

  it('test_feat_ins_001_validation_missing_vessel_id_shows_error_and_skips_creation', async () => {
    createInspectionPageMocks.useAuth.mockReturnValue({
      user: { user_type: 'vessel', role: 'VESSEL_MASTER', vessel_id: '' },
    });

    render(<CreateInspectionPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Submit' }));

    await waitFor(() => {
      expect(createInspectionPageMocks.createMutateAsync).not.toHaveBeenCalled();
      expect(createInspectionPageMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Error',
          variant: 'destructive',
        })
      );
    });
  });

  it('test_feat_ins_002_upload_failure_still_navigates_to_list_and_shows_warning', async () => {
    createInspectionPageMocks.uploadInspectionReport.mockRejectedValueOnce(
      new Error('upload failed')
    );

    render(<CreateInspectionPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Submit With Report' }));

    await waitFor(() => {
      expect(createInspectionPageMocks.uploadInspectionReport).toHaveBeenCalledTimes(1);
      expect(createInspectionPageMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Warning',
          variant: 'destructive',
        })
      );
      expect(createInspectionPageMocks.navigate).toHaveBeenCalledWith('/inspections', {
        replace: true,
      });
    });
  });

  it('test_feat_ins_001_cancel_confirmation_discards_and_navigates_back_to_list', async () => {
    render(<CreateInspectionPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Cancel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Discard' }));

    await waitFor(() => {
      expect(createInspectionPageMocks.navigate).toHaveBeenCalledWith('/inspections');
    });
  });
});
