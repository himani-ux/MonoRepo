/**
 * Tests for FEAT-DEF-002 route behavior on Register Follow-up page.
 *
 * PRD Reference: Docs/PRD.md Section 2.2 - FEAT-DEF-002
 * Flow Reference: Docs/APP_FLOW.md Section 2.2 (Register Follow-up)
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const followUpRouteMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  navigate: vi.fn(),
  useInspection: vi.fn(),
  useSubmitFollowUp: vi.fn(),
  useAuth: vi.fn(),
  toast: vi.fn(),
  mutateAsync: vi.fn(),
  wizardSubmitData: null as any,
}));

vi.mock('react-router-dom', () => ({
  useParams: () => followUpRouteMocks.useParams(),
  useNavigate: () => followUpRouteMocks.navigate,
}));

vi.mock('@/hooks/use-inspections', () => ({
  useInspection: (id: string) => followUpRouteMocks.useInspection(id),
  useSubmitFollowUp: () => followUpRouteMocks.useSubmitFollowUp(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => followUpRouteMocks.useAuth(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: followUpRouteMocks.toast }),
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

vi.mock('@/components/inspection/follow-up-wizard', () => ({
  FollowUpWizard: ({ onSubmit, onCancel }: any) => (
    <div>
      <button
        type="button"
        onClick={() =>
          onSubmit(followUpRouteMocks.wizardSubmitData)
        }
      >
        Trigger Submit
      </button>
      <button type="button" onClick={onCancel}>
        Trigger Cancel
      </button>
    </div>
  ),
}));

import RegisterFollowUpPage from './[id].follow-up';

function buildInspection(overrides: Record<string, unknown> = {}) {
  return {
    id: '123',
    inspection_type: 'PSC',
    ...overrides,
  } as any;
}

describe('RegisterFollowUpPage', () => {
  beforeEach(() => {
    followUpRouteMocks.useParams.mockReset();
    followUpRouteMocks.navigate.mockReset();
    followUpRouteMocks.useInspection.mockReset();
    followUpRouteMocks.useSubmitFollowUp.mockReset();
    followUpRouteMocks.useAuth.mockReset();
    followUpRouteMocks.toast.mockReset();
    followUpRouteMocks.mutateAsync.mockReset();
    followUpRouteMocks.wizardSubmitData = {
      reinspection_date: '2026-02-08',
      notes: 'Follow-up notes',
      deficiency_updates: [{ deficiency_id: 1, action_code_id: 10 }],
      report_file: null,
      report_description: '',
    };

    followUpRouteMocks.useParams.mockReturnValue({ id: '123' });
    followUpRouteMocks.useInspection.mockReturnValue({
      data: buildInspection(),
      isLoading: false,
      isError: false,
      error: null,
    });
    followUpRouteMocks.useAuth.mockReturnValue({
      user: { user_type: 'vessel', role: 'VESSEL_MASTER' },
    });
    followUpRouteMocks.mutateAsync.mockResolvedValue({
      data: {
        updated_deficiencies_count: 1,
      },
    });
    followUpRouteMocks.useSubmitFollowUp.mockReturnValue({
      mutateAsync: followUpRouteMocks.mutateAsync,
      isPending: false,
    });
  });

  it('test_feat_def_002_happy_path_submits_follow_up_and_navigates_to_new_inspection', async () => {
    render(<RegisterFollowUpPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Submit' }));

    await waitFor(() => {
      expect(followUpRouteMocks.mutateAsync).toHaveBeenCalledTimes(1);
      const formData = followUpRouteMocks.mutateAsync.mock.calls[0][0] as FormData;
      expect(formData).toBeInstanceOf(FormData);
      expect(formData.get('reinspection_date')).toBe('2026-02-08');
      expect(formData.get('notes')).toBe('Follow-up notes');
      expect(formData.get('deficiency_updates')).toBe(
        JSON.stringify([{ deficiency_id: 1, action_code_id: 10 }])
      );
      expect(followUpRouteMocks.navigate).toHaveBeenCalledWith('/inspections/123');
    });
  });

  it('test_feat_def_002_happy_path_submits_up_to_three_follow_up_report_pdfs', async () => {
    const reports = [
      new File(['pdf-one'], 'follow-up-one.pdf', { type: 'application/pdf' }),
      new File(['pdf-two'], 'follow-up-two.pdf', { type: 'application/pdf' }),
      new File(['pdf-three'], 'follow-up-three.pdf', { type: 'application/pdf' }),
    ];
    followUpRouteMocks.wizardSubmitData = {
      reinspection_date: '2026-02-08',
      notes: '',
      deficiency_updates: [{ deficiency_id: 1, action_code_id: 10 }],
      report_files: reports,
      report_description: 'Three supporting PDFs',
    };

    render(<RegisterFollowUpPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Submit' }));

    await waitFor(() => {
      expect(followUpRouteMocks.mutateAsync).toHaveBeenCalledTimes(1);
      const formData = followUpRouteMocks.mutateAsync.mock.calls[0][0] as FormData;
      expect(formData.getAll('report_files')).toEqual(reports);
      expect(formData.get('report_description')).toBe('Three supporting PDFs');
    });
  });

  it('test_feat_def_002_rbac_non_vessel_master_is_redirected_with_access_denied', async () => {
    followUpRouteMocks.useAuth.mockReturnValue({
      user: { user_type: 'office', role: 'OFFICE_PIC' },
    });

    render(<RegisterFollowUpPage />);

    await waitFor(() => {
      expect(followUpRouteMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Access Denied',
          variant: 'destructive',
        })
      );
      expect(followUpRouteMocks.navigate).toHaveBeenCalledWith('/inspections/123', {
        replace: true,
      });
    });
  });

  it('test_feat_def_002_precondition_non_psc_parent_is_redirected', async () => {
    followUpRouteMocks.useInspection.mockReturnValue({
      data: buildInspection({ inspection_type: 'RS' }),
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<RegisterFollowUpPage />);

    await waitFor(() => {
      expect(followUpRouteMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Invalid Inspection Type',
          variant: 'destructive',
        })
      );
      expect(followUpRouteMocks.navigate).toHaveBeenCalledWith('/inspections/123', {
        replace: true,
      });
    });
  });

  it('test_feat_def_002_cancel_returns_to_parent_inspection_detail', () => {
    render(<RegisterFollowUpPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Cancel' }));

    expect(followUpRouteMocks.navigate).toHaveBeenCalledWith('/inspections/123');
  });
});
