/**
 * Tests for FEAT-INS-007 and FEAT-INS-008 route-level edit behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-007, FEAT-INS-008
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const editPageMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  navigate: vi.fn(),
  useInspection: vi.fn(),
  useUpdateInspection: vi.fn(),
  useUploadInspectionReport: vi.fn(),
  useAuth: vi.fn(),
  toast: vi.fn(),
  updateMutateAsync: vi.fn(),
  uploadMutateAsync: vi.fn(),
  inspectionFormLastProps: null as any,
}));

vi.mock('react-router-dom', () => ({
  useParams: () => editPageMocks.useParams(),
  useNavigate: () => editPageMocks.navigate,
}));

vi.mock('@/hooks/use-inspections', () => ({
  useInspection: (id: string | number) => editPageMocks.useInspection(id),
  useUpdateInspection: (id: string | number) => editPageMocks.useUpdateInspection(id),
  useUploadInspectionReport: (id: string | number) => editPageMocks.useUploadInspectionReport(id),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => editPageMocks.useAuth(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: editPageMocks.toast }),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock('@/components/shared', () => ({
  FormSkeleton: () => <div>Form Skeleton</div>,
  ErrorState: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock('@/components/inspection', () => ({
  InspectionForm: (props: any) => {
    editPageMocks.inspectionFormLastProps = props;
    return (
      <div>
        <button
          type="button"
          onClick={() =>
            props.onSubmit(
              {
                inspection_type: 'PSC',
                psc_subtype: 'INITIAL',
                inspection_date: '2026-02-15',
                port: 'Singapore',
                port_state: 'SG',
                mou_code: 'TOKYO',
                authority: 'MPA',
                inspector_name: 'Inspector',
                report_reference: 'REF-1',
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
      </div>
    );
  },
}));

import EditInspectionPage from './[id].edit';

function buildInspection(overrides: Record<string, unknown> = {}) {
  return {
    id: 123,
    status: 'DRAFT',
    inspection_type: 'PSC',
    psc_subtype: 'INITIAL',
    inspection_date: '2026-02-01',
    port: 'Singapore',
    port_state: 'SG',
    mou_code: 'TOKYO',
    authority: 'MPA',
    inspector_name: 'John Inspector',
    report_reference: 'PSC-2026-001',
    is_detention: false,
    reports: [{ id: 1, file_path: '/uploads/report.pdf' }],
    ...overrides,
  } as any;
}

describe('EditInspectionPage', () => {
  beforeEach(() => {
    editPageMocks.useParams.mockReset();
    editPageMocks.navigate.mockReset();
    editPageMocks.useInspection.mockReset();
    editPageMocks.useUpdateInspection.mockReset();
    editPageMocks.useUploadInspectionReport.mockReset();
    editPageMocks.useAuth.mockReset();
    editPageMocks.toast.mockReset();
    editPageMocks.updateMutateAsync.mockReset();
    editPageMocks.uploadMutateAsync.mockReset();
    editPageMocks.inspectionFormLastProps = null;

    editPageMocks.useParams.mockReturnValue({ id: '123' });
    editPageMocks.updateMutateAsync.mockResolvedValue({});
    editPageMocks.uploadMutateAsync.mockResolvedValue({});

    editPageMocks.useUpdateInspection.mockReturnValue({
      mutateAsync: editPageMocks.updateMutateAsync,
      isPending: false,
    });
    editPageMocks.useUploadInspectionReport.mockReturnValue({
      mutateAsync: editPageMocks.uploadMutateAsync,
      isPending: false,
    });
  });

  it('test_feat_ins_007_happy_path_vessel_master_can_edit_draft_and_submit_update', async () => {
    editPageMocks.useAuth.mockReturnValue({
      user: { user_type: 'vessel', role: 'VESSEL_MASTER' },
    });
    editPageMocks.useInspection.mockReturnValue({
      data: buildInspection({ status: 'DRAFT' }),
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<EditInspectionPage />);

    expect(screen.getByText('Edit Inspection')).toBeInTheDocument();
    expect(editPageMocks.inspectionFormLastProps).toBeTruthy();
    expect(editPageMocks.inspectionFormLastProps.submitLabel).toBe('Save Changes');
    expect(editPageMocks.inspectionFormLastProps.existingReportUrl).toContain('/uploads/report.pdf');

    fireEvent.click(screen.getByRole('button', { name: 'Trigger Submit' }));

    await waitFor(() => {
      expect(editPageMocks.updateMutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(editPageMocks.updateMutateAsync).toHaveBeenCalledWith({
      inspection_type: 'PSC',
      psc_subtype: 'INITIAL',
      inspection_date: '2026-02-15',
      port_place: 'Singapore',
      country: 'SG',
      mou_id: 'TOKYO',
      authority: 'MPA',
      inspector_name: 'Inspector',
      is_detention: false,
      detention_reason: '',
      def_reported: 'NO',
    });
    expect(editPageMocks.navigate).toHaveBeenCalledWith('/inspections/123');
  });

  it('test_feat_ins_008_happy_path_office_can_edit_submitted_inspection', () => {
    editPageMocks.useAuth.mockReturnValue({
      user: { user_type: 'office', role: 'OFFICE_PIC' },
    });
    editPageMocks.useInspection.mockReturnValue({
      data: buildInspection({ status: 'SUBMITTED' }),
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<EditInspectionPage />);

    expect(screen.getByText('Edit Inspection')).toBeInTheDocument();
    expect(editPageMocks.inspectionFormLastProps).toBeTruthy();
    expect(editPageMocks.toast).not.toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Access Denied' })
    );
  });

  it('test_feat_ins_008_precondition_closed_inspection_redirects_with_access_denied', async () => {
    editPageMocks.useAuth.mockReturnValue({
      user: { user_type: 'office', role: 'OFFICE_PIC' },
    });
    editPageMocks.useInspection.mockReturnValue({
      data: buildInspection({ status: 'DPA_CLOSED' }),
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<EditInspectionPage />);

    await waitFor(() => {
      expect(editPageMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: 'destructive',
          title: 'Access Denied',
        })
      );
      expect(editPageMocks.navigate).toHaveBeenCalledWith('/inspections/123', {
        replace: true,
      });
    });
  });
});
