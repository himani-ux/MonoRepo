/**
 * Tests for page-header component behaviors used by FEAT-INS-010/FEAT-CAR-009 routes.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-010
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-009
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const pageHeaderMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => pageHeaderMocks.navigate,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({
    children,
    onClick,
    ...rest
  }: {
    children: React.ReactNode;
    onClick?: () => void;
  }) => (
    <button onClick={onClick} {...rest}>
      {children}
    </button>
  ),
}));

import { PageHeader } from './page-header';

describe('PageHeader', () => {
  beforeEach(() => {
    pageHeaderMocks.navigate.mockReset();
  });

  it('test_feat_ins_010_renders_title_subtitle_and_actions', () => {
    render(
      <PageHeader
        title="Inspections"
        subtitle="PSC, RightShip, Audit"
        actions={<button>Extra Action</button>}
      />
    );

    expect(screen.getByText('Inspections')).toBeInTheDocument();
    expect(screen.getByText('PSC, RightShip, Audit')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Extra Action' })).toBeInTheDocument();
  });

  it('test_feat_ins_010_back_button_without_backto_uses_history_back', () => {
    render(<PageHeader title="Detail" showBack />);

    fireEvent.click(screen.getByRole('button', { name: /go back/i }));

    expect(pageHeaderMocks.navigate).toHaveBeenCalledWith(-1);
  });

  it('test_feat_car_009_back_button_with_backto_navigates_to_provided_path', () => {
    render(<PageHeader title="CAR Detail" showBack backTo="/cars" />);

    fireEvent.click(screen.getByRole('button', { name: /go back/i }));

    expect(pageHeaderMocks.navigate).toHaveBeenCalledWith('/cars');
  });
});

