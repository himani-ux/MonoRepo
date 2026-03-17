/**
 * Tests for root layout authenticated shell behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-001
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const rootLayoutMocks = vi.hoisted(() => ({
  useRequireAuth: vi.fn(),
  useOffline: vi.fn(),
  headerProps: null as any,
  sidebarProps: [] as any[],
}));

vi.mock('@/hooks/use-auth', () => ({
  useRequireAuth: () => rootLayoutMocks.useRequireAuth(),
}));

vi.mock('@/hooks/use-offline', () => ({
  useOffline: () => rootLayoutMocks.useOffline(),
}));

vi.mock('./header', () => ({
  Header: (props: any) => {
    rootLayoutMocks.headerProps = props;
    return (
      <button onClick={props.onMenuClick}>
        Header
      </button>
    );
  },
}));

vi.mock('./sidebar', () => ({
  Sidebar: (props: any) => {
    rootLayoutMocks.sidebarProps.push(props);
    return <div>{`Sidebar:${props.isOpen ? 'open' : 'closed'}`}</div>;
  },
}));

vi.mock('./bottom-nav', () => ({
  BottomNav: () => <div>BottomNav</div>,
}));

vi.mock('@/components/sync/offline-banner', () => ({
  OfflineBanner: ({ isOnline }: { isOnline: boolean }) => (
    <div>{`OfflineBanner:${isOnline ? 'online' : 'offline'}`}</div>
  ),
}));

import { RootLayout } from './root-layout';

describe('RootLayout', () => {
  beforeEach(() => {
    rootLayoutMocks.useRequireAuth.mockReset();
    rootLayoutMocks.useOffline.mockReset();
    rootLayoutMocks.headerProps = null;
    rootLayoutMocks.sidebarProps = [];

    rootLayoutMocks.useRequireAuth.mockReturnValue({ isLoading: false });
    rootLayoutMocks.useOffline.mockReturnValue({
      isOnline: true,
      lastSyncTime: null,
    });
  });

  it('test_feat_sync_001_shows_spinner_while_auth_loading', () => {
    rootLayoutMocks.useRequireAuth.mockReturnValue({ isLoading: true });

    const { container } = render(
      <RootLayout>
        <div>Content</div>
      </RootLayout>
    );

    expect(container.querySelector('.animate-spin')).not.toBeNull();
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('test_feat_sync_001_hide_navigation_mode_renders_header_banner_and_content_without_side_nav', () => {
    render(
      <RootLayout hideNavigation>
        <div>Minimal Content</div>
      </RootLayout>
    );

    expect(screen.getByText('Header')).toBeInTheDocument();
    expect(screen.getByText('OfflineBanner:online')).toBeInTheDocument();
    expect(screen.getByText('Minimal Content')).toBeInTheDocument();
    expect(screen.queryByText('BottomNav')).not.toBeInTheDocument();
  });

  it('test_feat_sync_001_default_layout_opens_mobile_sidebar_on_menu_click', () => {
    render(
      <RootLayout>
        <div>Page Body</div>
      </RootLayout>
    );

    fireEvent.click(screen.getByText('Header'));

    expect(screen.getAllByText(/Sidebar:/).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('BottomNav')).toBeInTheDocument();
    expect(screen.getByText('Page Body')).toBeInTheDocument();
  });
});

