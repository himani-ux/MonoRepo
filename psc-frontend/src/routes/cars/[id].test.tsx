/**
 * Tests for FEAT-PV-002 route-level close permission gating on CAR detail page.
 *
 * PRD Reference: Docs/PRD.md Section 2.4 - FEAT-PV-002
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const carDetailPageMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  navigate: vi.fn(),
  useCAR: vi.fn(),
  useSubmitCAR: vi.fn(),
  useReopenCAR: vi.fn(),
  useAuth: vi.fn(),
  toast: vi.fn(),
  physicalVerificationProps: null as any,
}));

vi.mock('react-router-dom', () => ({
  useParams: () => carDetailPageMocks.useParams(),
  useNavigate: () => carDetailPageMocks.navigate,
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
}));

vi.mock('@/hooks/use-cars', () => ({
  useCAR: (id: string | number) => carDetailPageMocks.useCAR(id),
  useSubmitCAR: () => carDetailPageMocks.useSubmitCAR(),
  useReopenCAR: () => carDetailPageMocks.useReopenCAR(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => carDetailPageMocks.useAuth(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: carDetailPageMocks.toast }),
}));

vi.mock('@/lib/api/cars', () => ({
  exportCARPDF: vi.fn(),
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
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    asChild?: boolean;
  }) => (asChild ? children : <button onClick={onClick}>{children}</button>),
  DropdownMenuSeparator: () => <hr />,
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({
    title,
    actions,
  }: {
    title: string;
    actions?: React.ReactNode;
  }) => (
    <div>
      <h1>{title}</h1>
      {actions}
    </div>
  ),
}));

vi.mock('@/components/shared', () => ({
  ErrorState: ({ title }: { title: string }) => <div>{title}</div>,
  ConfirmDialog: () => null,
  SubmitConfirmDialog: () => null,
}));

vi.mock('@/components/shared/loading-skeleton', () => ({
  DetailHeaderSkeleton: () => <div>Header Skeleton</div>,
  SectionSkeleton: () => <div>Section Skeleton</div>,
}));

vi.mock('@/components/car/car-detail', () => ({
  CARDetail: () => <div>CAR Detail</div>,
}));
vi.mock('@/components/car/car-workflow-actions', () => ({
  CARWorkflowActions: () => null,
}));
vi.mock('@/components/car/evidence-upload-modal', () => ({
  EvidenceUploadModal: () => null,
}));
vi.mock('@/components/car/pic-accept-modal', () => ({
  PICAcceptModal: () => null,
}));
vi.mock('@/components/car/rework-modal', () => ({
  ReworkModal: () => null,
}));
vi.mock('@/components/car/dpa-close-modal', () => ({
  DPACloseModal: () => null,
}));
vi.mock('@/components/car/pv-create-modal', () => ({
  PVCreateModal: () => null,
}));
vi.mock('@/components/car/pv-close-modal', () => ({
  PVCloseModal: () => null,
}));
vi.mock('@/components/car/physical-verification-section', () => ({
  PhysicalVerificationSection: (props: any) => {
    carDetailPageMocks.physicalVerificationProps = props;
    return <div>canClosePV:{String(props.canClosePV)}</div>;
  },
}));

import CARDetailPage from './[id]';
import { exportCARPDF } from '@/lib/api/cars';

function buildCar(overrides: Record<string, unknown> = {}) {
  return {
    id: 3001,
    car_number: 'PSC-2026-001',
    status: 'DPA_CLOSED',
    physical_verification: {
      id: 1,
      status: 'OPEN',
      verifier_user_id: 'EMP999',
    },
    ...overrides,
  } as any;
}

describe('CARDetailPage', () => {
  const mockedExportCARPDF = vi.mocked(exportCARPDF);

  beforeEach(() => {
    carDetailPageMocks.useParams.mockReset();
    carDetailPageMocks.navigate.mockReset();
    carDetailPageMocks.useCAR.mockReset();
    carDetailPageMocks.useSubmitCAR.mockReset();
    carDetailPageMocks.useReopenCAR.mockReset();
    carDetailPageMocks.useAuth.mockReset();
    carDetailPageMocks.toast.mockReset();
    carDetailPageMocks.physicalVerificationProps = null;
    mockedExportCARPDF.mockReset();

    carDetailPageMocks.useParams.mockReturnValue({ id: '3001' });
    carDetailPageMocks.useSubmitCAR.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
    carDetailPageMocks.useReopenCAR.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
  });

  it('test_feat_pv_002_office_user_cannot_close_when_not_assigned_verifier', () => {
    carDetailPageMocks.useAuth.mockReturnValue({
      user: { id: 'EMP001', employee_id: 'EMP001' },
      isVessel: false,
      isOffice: true,
      isDPA: false,
      isPIC: false,
    });
    carDetailPageMocks.useCAR.mockReturnValue({
      data: buildCar({ physical_verification: { id: 1, status: 'OPEN', verifier_user_id: 'EMP999' } }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<CARDetailPage />);
    expect(screen.getByText('canClosePV:false')).toBeInTheDocument();
  });

  it('test_feat_pv_002_office_assigned_verifier_can_close_with_normalized_id_match', () => {
    carDetailPageMocks.useAuth.mockReturnValue({
      user: { id: 'EMP001', employee_id: ' emp001 ' },
      isVessel: false,
      isOffice: true,
      isDPA: false,
      isPIC: true,
    });
    carDetailPageMocks.useCAR.mockReturnValue({
      data: buildCar({ physical_verification: { id: 1, status: 'OPEN', verifier_user_id: 'EMP001' } }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<CARDetailPage />);
    expect(screen.getByText('canClosePV:true')).toBeInTheDocument();
  });

  it('test_feat_pv_002_dpa_can_close_even_when_not_assigned_verifier', () => {
    carDetailPageMocks.useAuth.mockReturnValue({
      user: { id: 'EMP777', employee_id: 'EMP777' },
      isVessel: false,
      isOffice: true,
      isDPA: true,
      isPIC: false,
    });
    carDetailPageMocks.useCAR.mockReturnValue({
      data: buildCar({ physical_verification: { id: 1, status: 'OPEN', verifier_user_id: 'EMP999' } }),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<CARDetailPage />);
    expect(screen.getByText('canClosePV:true')).toBeInTheDocument();
  });

  it('test_feat_rpt_001_route_shows_external_and_internal_download_choices', () => {
    carDetailPageMocks.useAuth.mockReturnValue({
      user: { id: 'EMP001', employee_id: 'EMP001' },
      isVessel: false,
      isOffice: true,
      isDPA: false,
      isPIC: true,
    });
    carDetailPageMocks.useCAR.mockReturnValue({
      data: buildCar(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<CARDetailPage />);
    expect(screen.getByText('Download (External)')).toBeInTheDocument();
    expect(screen.getByText('Download (Internal)')).toBeInTheDocument();
  });

  it('test_feat_rpt_001_route_passes_external_audience_when_external_download_clicked', async () => {
    carDetailPageMocks.useAuth.mockReturnValue({
      user: { id: 'EMP001', employee_id: 'EMP001' },
      isVessel: false,
      isOffice: true,
      isDPA: false,
      isPIC: true,
    });
    carDetailPageMocks.useCAR.mockReturnValue({
      data: buildCar(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    mockedExportCARPDF.mockRejectedValueOnce(new Error('mock export failure'));

    render(<CARDetailPage />);
    fireEvent.click(screen.getByText('Download (External)'));

    await waitFor(() => {
      expect(mockedExportCARPDF).toHaveBeenCalledWith('3001', 'external');
    });
  });

  it('test_feat_rpt_001_route_passes_internal_audience_when_internal_download_clicked', async () => {
    carDetailPageMocks.useAuth.mockReturnValue({
      user: { id: 'EMP001', employee_id: 'EMP001' },
      isVessel: false,
      isOffice: true,
      isDPA: false,
      isPIC: true,
    });
    carDetailPageMocks.useCAR.mockReturnValue({
      data: buildCar(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    mockedExportCARPDF.mockRejectedValueOnce(new Error('mock export failure'));

    render(<CARDetailPage />);
    fireEvent.click(screen.getByText('Download (Internal)'));

    await waitFor(() => {
      expect(mockedExportCARPDF).toHaveBeenCalledWith('3001', 'internal');
    });
  });
});
