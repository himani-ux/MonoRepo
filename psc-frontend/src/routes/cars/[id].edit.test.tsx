/**
 * Tests for FEAT-CAR-002 route behavior on Edit CAR page.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-002
 * Flow Reference: Docs/APP_FLOW.md Section 2.3 (Edit CAR)
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const editCarRouteMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  navigate: vi.fn(),
  useCAR: vi.fn(),
  useUpdateCAR: vi.fn(),
  useTransitionCAR: vi.fn(),
  useCARAvailableActions: vi.fn(),
  useAuth: vi.fn(),
  toast: vi.fn(),
  updateMutateAsync: vi.fn(),
  transitionMutateAsync: vi.fn(),
  carFormProps: null as any,
}));

vi.mock('react-router-dom', () => ({
  useParams: () => editCarRouteMocks.useParams(),
  useNavigate: () => editCarRouteMocks.navigate,
}));

vi.mock('@/hooks/use-cars', () => ({
  useCAR: (id: string) => editCarRouteMocks.useCAR(id),
  useUpdateCAR: (_id: string) => editCarRouteMocks.useUpdateCAR(),
  useTransitionCAR: (_id: string) => editCarRouteMocks.useTransitionCAR(),
  useCARAvailableActions: (_id: string) => editCarRouteMocks.useCARAvailableActions(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => editCarRouteMocks.useAuth(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: editCarRouteMocks.toast }),
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

vi.mock('@/components/car', () => ({
  CARForm: (props: any) => {
    editCarRouteMocks.carFormProps = props;
    return (
      <div>
        <button
          type="button"
          onClick={() =>
            props.onSaveDraft({
              root_cause_summary:
                'This is a sufficiently long root cause summary for save draft testing.',
              target_date: '2026-02-15',
              clc_item_ids: ['clc-1'],
              custom_cause_text: 'Custom text',
            })
          }
        >
          Trigger Save Draft
        </button>
        <button type="button" onClick={props.onCancel}>
          Trigger Cancel
        </button>
      </div>
    );
  },
  EvidenceUploadModal: () => null,
}));

import EditCARPage from './[id].edit';

function buildCar(overrides: Record<string, unknown> = {}) {
  return {
    id: 'car-1',
    car_number: 'PSC-2026-001',
    status: 'ALLOTTED',
    ...overrides,
  } as any;
}

describe('EditCARPage', () => {
  beforeEach(() => {
    editCarRouteMocks.useParams.mockReset();
    editCarRouteMocks.navigate.mockReset();
    editCarRouteMocks.useCAR.mockReset();
    editCarRouteMocks.useUpdateCAR.mockReset();
    editCarRouteMocks.useTransitionCAR.mockReset();
    editCarRouteMocks.useCARAvailableActions.mockReset();
    editCarRouteMocks.useAuth.mockReset();
    editCarRouteMocks.toast.mockReset();
    editCarRouteMocks.updateMutateAsync.mockReset();
    editCarRouteMocks.transitionMutateAsync.mockReset();
    editCarRouteMocks.carFormProps = null;

    editCarRouteMocks.useParams.mockReturnValue({ id: 'car-1' });
    editCarRouteMocks.useCAR.mockReturnValue({
      data: buildCar({ status: 'ALLOTTED' }),
      isLoading: false,
      isError: false,
      error: null,
    });
    editCarRouteMocks.useAuth.mockReturnValue({
      user: { user_type: 'vessel', role: 'VESSEL_MASTER' },
    });
    editCarRouteMocks.useUpdateCAR.mockReturnValue({
      mutateAsync: editCarRouteMocks.updateMutateAsync,
      isPending: false,
    });
    editCarRouteMocks.useTransitionCAR.mockReturnValue({
      mutateAsync: editCarRouteMocks.transitionMutateAsync,
      isPending: false,
    });
    editCarRouteMocks.useCARAvailableActions.mockReturnValue({ data: [] });
    editCarRouteMocks.updateMutateAsync.mockResolvedValue({});
    editCarRouteMocks.transitionMutateAsync.mockResolvedValue({});
  });

  it('test_feat_car_002_happy_path_vessel_master_saves_draft', async () => {
    render(<EditCARPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Save Draft' }));

    await waitFor(() => {
      expect(editCarRouteMocks.updateMutateAsync).toHaveBeenCalledWith({
        root_cause_summary:
          'This is a sufficiently long root cause summary for save draft testing.',
        target_date: '2026-02-15',
        clc_item_ids: ['clc-1'],
        custom_cause_text: 'Custom text',
      });
      expect(editCarRouteMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'CAR Saved',
        })
      );
    });
  });

  it('test_feat_car_002_office_user_can_edit_submitted_car', () => {
    editCarRouteMocks.useAuth.mockReturnValue({
      user: { user_type: 'office', role: 'OFFICE_PIC' },
    });
    editCarRouteMocks.useCAR.mockReturnValue({
      data: buildCar({ status: 'SUBMITTED' }),
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<EditCARPage />);

    expect(editCarRouteMocks.carFormProps).toBeTruthy();
    expect(editCarRouteMocks.toast).not.toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Access Denied' })
    );
  });

  it('test_feat_car_002_vessel_cannot_edit_submitted_car_and_is_redirected', async () => {
    editCarRouteMocks.useCAR.mockReturnValue({
      data: buildCar({ status: 'SUBMITTED' }),
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<EditCARPage />);

    await waitFor(() => {
      expect(editCarRouteMocks.toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Access Denied',
          variant: 'destructive',
        })
      );
      expect(editCarRouteMocks.navigate).toHaveBeenCalledWith('/cars/car-1', {
        replace: true,
      });
    });
  });

  it('test_feat_car_002_cancel_returns_to_car_detail', () => {
    render(<EditCARPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Trigger Cancel' }));

    expect(editCarRouteMocks.navigate).toHaveBeenCalledWith('/cars/car-1');
  });
});
