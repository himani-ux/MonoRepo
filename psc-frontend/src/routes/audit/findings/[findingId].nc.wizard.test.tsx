import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const ncWizardRouteMocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  ncClosurePage: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useParams: () => ncWizardRouteMocks.useParams(),
}));

vi.mock('@/components/audit/finding/audit-nc-closure-page', () => ({
  AuditNcClosurePage: ({ findingId }: { findingId: string }) => {
    ncWizardRouteMocks.ncClosurePage({ findingId });
    return <div>Dense NC Closure {findingId}</div>;
  },
}));

import AuditNcWizardRoute from './[findingId].nc.wizard';

describe('AuditNcWizardRoute', () => {
  beforeEach(() => {
    ncWizardRouteMocks.useParams.mockReset();
    ncWizardRouteMocks.ncClosurePage.mockReset();
    ncWizardRouteMocks.useParams.mockReturnValue({ findingId: 'finding-1' });
  });

  it('keeps the legacy NC wizard URL on the dense NC closure page', () => {
    render(<AuditNcWizardRoute />);

    expect(screen.getByText('Dense NC Closure finding-1')).toBeInTheDocument();
    expect(ncWizardRouteMocks.ncClosurePage).toHaveBeenCalledWith({ findingId: 'finding-1' });
  });
});
