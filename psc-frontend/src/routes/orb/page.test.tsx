import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const orbRouteMocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  Navigate: ({ to }: { to: string }) => <div>Navigate:{to}</div>,
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => orbRouteMocks.useAuth(),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: ReactNode }) => <div data-testid="root-layout">{children}</div>,
}));

vi.mock('@/legacy/vims-basic/module-provider', () => ({
  LegacyBasicProvider: ({ children }: { children: ReactNode }) => (
    <div data-testid="legacy-provider">{children}</div>
  ),
}));

vi.mock('@/legacy/vims-basic/routes/orb/OrbRoutes.jsx', () => ({
  default: () => <div>Legacy ORB Routes</div>,
}));

vi.mock('./office-approved-entries', () => ({
  default: () => <div>Office ORB Approved Entries</div>,
}));

import { ORBModulePage } from './page';

describe('ORBModulePage', () => {
  beforeEach(() => {
    orbRouteMocks.useAuth.mockReset();
  });

  it('redirects unauthenticated users to login', () => {
    orbRouteMocks.useAuth.mockReturnValue({
      isAuthenticated: false,
      isOffice: false,
      isVessel: false,
    });

    render(<ORBModulePage />);

    expect(screen.getByText('Navigate:/login')).toBeInTheDocument();
  });

  it('renders legacy shipside orb module for vessel users', () => {
    orbRouteMocks.useAuth.mockReturnValue({
      isAuthenticated: true,
      isOffice: false,
      isVessel: true,
    });

    render(<ORBModulePage />);

    expect(screen.getByTestId('legacy-provider')).toBeInTheDocument();
    expect(screen.getByText('Legacy ORB Routes')).toBeInTheDocument();
  });

  it('renders native office orb approved-entry page for office users', () => {
    orbRouteMocks.useAuth.mockReturnValue({
      isAuthenticated: true,
      isOffice: true,
      isVessel: false,
    });

    render(<ORBModulePage />);

    expect(screen.getByTestId('root-layout')).toBeInTheDocument();
    expect(screen.getByText('Office ORB Approved Entries')).toBeInTheDocument();
  });
});
