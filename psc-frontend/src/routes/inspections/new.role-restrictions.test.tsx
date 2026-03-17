import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { INSPECTION_TYPES, USER_ROLES } from '@/lib/utils/constants';

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  useAuth: vi.fn(),
  toast: vi.fn(),
  useCreateInspection: vi.fn(),
  createMutateAsync: vi.fn(),
  uploadInspectionReport: vi.fn(),
  inspectionFormProps: null as any,
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => mocks.navigate,
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => mocks.useAuth(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mocks.toast }),
}));

vi.mock('@/hooks/use-inspections', () => ({
  useCreateInspection: () => mocks.useCreateInspection(),
}));

vi.mock('@/lib/api/inspections', () => ({
  inspectionsApi: {
    uploadInspectionReport: (...args: unknown[]) => mocks.uploadInspectionReport(...args),
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
  ConfirmDialog: () => null,
}));

vi.mock('@/components/inspection/inspection-form', () => ({
  InspectionForm: (props: any) => {
    mocks.inspectionFormProps = props;
    return (
      <div>
        <button
          type="button"
          onClick={() =>
            props.onSubmit(
              {
                inspection_type: INSPECTION_TYPES.PSC,
                psc_subtype: 'INITIAL',
                inspection_date: '2026-02-08',
                port: 'Singapore',
                port_state: 'SG',
                mou_code: 'TOKYO',
                authority: 'Authority',
                inspector_name: 'Inspector',
                is_detention: false,
                detention_reason: null,
                def_reported: 'NO',
              },
              null
            )
          }
        >
          Submit PSC
        </button>
        <button
          type="button"
          onClick={() =>
            props.onSubmit(
              {
                inspection_type: INSPECTION_TYPES.AUDIT,
                psc_subtype: null,
                inspection_date: '2026-02-08',
                port: 'Singapore',
                port_state: 'SG',
                mou_code: null,
                authority: 'Authority',
                inspector_name: 'Inspector',
                is_detention: false,
                detention_reason: null,
                def_reported: 'NO',
              },
              null
            )
          }
        >
          Submit Audit
        </button>
      </div>
    );
  },
}));

import CreateInspectionPage from './new';

describe('CreateInspectionPage RBAC type restrictions', () => {
  beforeEach(() => {
    mocks.navigate.mockReset();
    mocks.useAuth.mockReset();
    mocks.toast.mockReset();
    mocks.useCreateInspection.mockReset();
    mocks.createMutateAsync.mockReset();
    mocks.uploadInspectionReport.mockReset();
    mocks.inspectionFormProps = null;

    mocks.createMutateAsync.mockResolvedValue({ id: 'ins-100' });
    mocks.useCreateInspection.mockReturnValue({
      mutateAsync: mocks.createMutateAsync,
      isPending: false,
    });
  });

  it('office user sees only AUDIT type and cannot submit PSC', async () => {
    mocks.useAuth.mockReturnValue({
      user: {
        role: USER_ROLES.OFFICE_PIC,
        vessel_id: 'vessel-1',
      },
    });

    render(<CreateInspectionPage />);

    expect(mocks.inspectionFormProps.allowedInspectionTypes).toEqual([
      INSPECTION_TYPES.AUDIT,
    ]);

    fireEvent.click(screen.getByRole('button', { name: 'Submit PSC' }));

    await waitFor(() => {
      expect(mocks.createMutateAsync).not.toHaveBeenCalled();
      expect(mocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Access denied',
          variant: 'destructive',
        })
      );
    });
  });

  it('office user can still submit AUDIT', async () => {
    mocks.useAuth.mockReturnValue({
      user: {
        role: USER_ROLES.OFFICE_PIC,
        vessel_id: 'vessel-1',
      },
    });

    render(<CreateInspectionPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Submit Audit' }));

    await waitFor(() => {
      expect(mocks.createMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          inspection_type: INSPECTION_TYPES.AUDIT,
          vessel_id: 'vessel-1',
        })
      );
      expect(mocks.navigate).toHaveBeenCalledWith('/inspections/ins-100');
    });
  });

  it('vessel master can submit PSC and gets all type options', async () => {
    mocks.useAuth.mockReturnValue({
      user: {
        role: USER_ROLES.VESSEL_MASTER,
        vessel_id: 'vessel-1',
      },
    });

    render(<CreateInspectionPage />);

    expect(mocks.inspectionFormProps.allowedInspectionTypes).toEqual([
      INSPECTION_TYPES.PSC,
      INSPECTION_TYPES.RS,
      INSPECTION_TYPES.AUDIT,
    ]);

    fireEvent.click(screen.getByRole('button', { name: 'Submit PSC' }));

    await waitFor(() => {
      expect(mocks.createMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          inspection_type: INSPECTION_TYPES.PSC,
          vessel_id: 'vessel-1',
        })
      );
      expect(mocks.navigate).toHaveBeenCalledWith('/inspections/ins-100');
    });
  });
});
