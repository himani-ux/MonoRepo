/**
 * Tests for FEAT-INS-009 route-level delete behavior on Inspection Detail page.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-009
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const inspectionDetailPageMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  navigate: vi.fn(),
  useInspection: vi.fn(),
  useDeleteInspection: vi.fn(),
  useSubmitInspection: vi.fn(),
  usePICReviewInspection: vi.fn(),
  useDPACloseInspection: vi.fn(),
  useAuth: vi.fn(),
  toast: vi.fn(),
  deleteMutateAsync: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useParams: () => inspectionDetailPageMocks.useParams(),
  useNavigate: () => inspectionDetailPageMocks.navigate,
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
}));

vi.mock('@/hooks/use-inspections', () => ({
  useInspection: (id: string | number) => inspectionDetailPageMocks.useInspection(id),
  useDeleteInspection: () => inspectionDetailPageMocks.useDeleteInspection(),
  useSubmitInspection: () => inspectionDetailPageMocks.useSubmitInspection(),
  usePICReviewInspection: () => inspectionDetailPageMocks.usePICReviewInspection(),
  useDPACloseInspection: () => inspectionDetailPageMocks.useDPACloseInspection(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => inspectionDetailPageMocks.useAuth(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: inspectionDetailPageMocks.toast }),
}));

vi.mock('@/components/ui', () => ({
  Button: ({
    children,
    onClick,
    asChild,
    ...rest
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    asChild?: boolean;
  }) => (asChild ? children : <button onClick={onClick} {...rest}>{children}</button>),
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({
    children,
    onClick,
    asChild,
    className,
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    asChild?: boolean;
    className?: string;
  }) => (asChild ? children : <button className={className} onClick={onClick}>{children}</button>),
  DropdownMenuSeparator: () => <hr />,
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title, actions }: { title: string; actions?: React.ReactNode }) => (
    <div>
      <h1>{title}</h1>
      {actions}
    </div>
  ),
}));

vi.mock('@/components/shared', () => ({
  ErrorState: ({ title }: { title: string }) => <div>{title}</div>,
  DeleteConfirmDialog: ({
    open,
    onConfirm,
  }: {
    open: boolean;
    onConfirm: () => void;
  }) => (open ? <button onClick={onConfirm}>Confirm Delete</button> : null),
  SubmitConfirmDialog: () => null,
  ConfirmDialog: () => null,
  DetailHeaderSkeleton: () => <div>Detail Skeleton</div>,
  SectionSkeleton: () => <div>Section Skeleton</div>,
}));

vi.mock('@/components/inspection', () => ({
  InspectionDetail: () => <div>Inspection Detail Content</div>,
  DeficiencyModal: () => null,
  InspectionPICReviewModal: () => null,
  InspectionDPACloseModal: () => null,
}));

import InspectionDetailPage from './[id]';

function buildInspection(overrides: Record<string, unknown> = {}) {
  return {
    id: 123,
    status: 'DRAFT',
    inspection_type: 'PSC',
    reports: [{ id: 1, file_path: '/uploads/report.pdf' }],
    ...overrides,
  } as any;
}

describe('InspectionDetailPage', () => {
  beforeEach(() => {
    inspectionDetailPageMocks.useParams.mockReset();
    inspectionDetailPageMocks.navigate.mockReset();
    inspectionDetailPageMocks.useInspection.mockReset();
    inspectionDetailPageMocks.useDeleteInspection.mockReset();
    inspectionDetailPageMocks.useSubmitInspection.mockReset();
    inspectionDetailPageMocks.usePICReviewInspection.mockReset();
    inspectionDetailPageMocks.useDPACloseInspection.mockReset();
    inspectionDetailPageMocks.useAuth.mockReset();
    inspectionDetailPageMocks.toast.mockReset();
    inspectionDetailPageMocks.deleteMutateAsync.mockReset();

    inspectionDetailPageMocks.useParams.mockReturnValue({ id: '123' });
    inspectionDetailPageMocks.deleteMutateAsync.mockResolvedValue({});
    inspectionDetailPageMocks.useDeleteInspection.mockReturnValue({
      mutateAsync: inspectionDetailPageMocks.deleteMutateAsync,
      isPending: false,
    });
    inspectionDetailPageMocks.useSubmitInspection.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
    inspectionDetailPageMocks.usePICReviewInspection.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
    inspectionDetailPageMocks.useDPACloseInspection.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
  });

  it('test_feat_ins_009_happy_path_vessel_master_can_delete_draft_and_redirect', async () => {
    inspectionDetailPageMocks.useAuth.mockReturnValue({
      isVessel: true,
      isOffice: false,
      isDPA: false,
      isPIC: false,
    });
    inspectionDetailPageMocks.useInspection.mockReturnValue({
      data: buildInspection({ status: 'DRAFT' }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<InspectionDetailPage />);

    fireEvent.click(screen.getByRole('button', { name: /delete inspection/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Delete' }));

    await waitFor(() => {
      expect(inspectionDetailPageMocks.deleteMutateAsync).toHaveBeenCalledWith('123');
    });
    expect(inspectionDetailPageMocks.toast).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Inspection deleted',
      })
    );
    expect(inspectionDetailPageMocks.navigate).toHaveBeenCalledWith('/inspections');
  });

  it('test_feat_ins_009_rbac_office_user_does_not_see_delete_action', () => {
    inspectionDetailPageMocks.useAuth.mockReturnValue({
      isVessel: false,
      isOffice: true,
      isDPA: false,
      isPIC: true,
    });
    inspectionDetailPageMocks.useInspection.mockReturnValue({
      data: buildInspection({ status: 'DRAFT' }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<InspectionDetailPage />);
    expect(screen.queryByRole('button', { name: /delete inspection/i })).not.toBeInTheDocument();
  });
});
