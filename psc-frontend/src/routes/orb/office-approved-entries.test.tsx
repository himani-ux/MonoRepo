import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const officeOrbMocks = vi.hoisted(() => ({
  fetchVessels: vi.fn(),
  fetchApprovedEntries: vi.fn(),
}));

vi.mock('@/lib/api/orb', () => ({
  orbApi: {
    fetchVessels: (...args: unknown[]) => officeOrbMocks.fetchVessels(...args),
    fetchApprovedEntries: (...args: unknown[]) => officeOrbMocks.fetchApprovedEntries(...args),
  },
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title, subtitle }: { title: string; subtitle?: string }) => (
    <header>
      <h1>{title}</h1>
      {subtitle ? <p>{subtitle}</p> : null}
    </header>
  ),
}));

vi.mock('@/components/shared/date-picker', () => ({
  DatePicker: ({
    value,
    onChange,
    id,
    maxDate,
    minDate,
    ...rest
  }: {
    value?: string;
    onChange?: (value: string) => void;
    id?: string;
    maxDate?: string;
    minDate?: string;
  }) => (
    <input
      id={id}
      type="date"
      value={value || ''}
      max={maxDate}
      min={minDate}
      onChange={(event) => onChange?.(event.target.value)}
      {...rest}
    />
  ),
}));

vi.mock('@/components/shared', () => ({
  EmptyState: ({ title, description }: { title: string; description?: string }) => (
    <div>
      <p>{title}</p>
      {description ? <p>{description}</p> : null}
    </div>
  ),
  ErrorState: ({ title, message }: { title: string; message?: string }) => (
    <div>
      <p>{title}</p>
      {message ? <p>{message}</p> : null}
    </div>
  ),
}));

vi.mock('@/components/ui', () => ({
  Button: ({
    children,
    onClick,
    ...rest
  }: {
    children: ReactNode;
    onClick?: () => void;
  }) => (
    <button onClick={onClick} {...rest}>
      {children}
    </button>
  ),
  Card: ({ children }: { children: ReactNode }) => <section>{children}</section>,
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  CardDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Label: ({
    children,
    htmlFor,
  }: {
    children: ReactNode;
    htmlFor?: string;
  }) => <label htmlFor={htmlFor}>{children}</label>,
  Select: ({
    value,
    onValueChange,
    children,
  }: {
    value: string;
    onValueChange?: (value: string) => void;
    children: ReactNode;
  }) => (
    <select value={value} onChange={(event) => onValueChange?.(event.target.value)}>
      {children}
    </select>
  ),
  SelectTrigger: () => null,
  SelectValue: () => null,
  SelectContent: ({ children }: { children: ReactNode }) => <>{children}</>,
  SelectItem: ({ value, children }: { value: string; children: ReactNode }) => (
    <option value={value}>{children}</option>
  ),
  Skeleton: () => <div>Loading</div>,
}));

import OfficeORBApprovedEntriesPage from './office-approved-entries';

describe('OfficeORBApprovedEntriesPage', () => {
  beforeEach(() => {
    officeOrbMocks.fetchVessels.mockReset();
    officeOrbMocks.fetchApprovedEntries.mockReset();

    officeOrbMocks.fetchVessels.mockResolvedValue([
      { id: 'v-1', vesselName: 'MV Alpha', vesselCode: 'ALP' },
      { id: 'v-2', vesselName: 'MV Bravo', vesselCode: 'BRV' },
    ]);
    officeOrbMocks.fetchApprovedEntries.mockImplementation((vesselId: string) => {
      if (vesselId === 'v-1') {
        return Promise.resolve([
          {
            id: 'entry-a',
            date: '2026-01-10T09:00:00Z',
            code: 'A',
            item_no: '1',
            record_of_operation: [
              'Alpha record',
              'TANK(S) BALLASTED',
              `NOT CLEANED \u2013 PREVIOUS OIL`,
              'START BALLAST',
            ].join('\n'),
            status: 'Approved',
            approved_by: 'Chief Alpha',
            approved_at: '2026-01-10T10:00:00Z',
          },
        ]);
      }

      return Promise.resolve([
        {
          id: 'entry-b',
          date: '2026-03-15T09:00:00Z',
          code: 'B',
          item_no: '6',
          record_of_operation: [
            'Bravo record',
            `END POSITION 12\u00b015'N 079\u00b030'E`,
            '12 KNOTS',
            'THROUGH 15 PPM EQUIPMENT',
            `15 ${`M\u00b3`}`,
            'SIGNED: Chief Officer',
          ].join('\n'),
          status: 'Approved',
          approved_by: 'Chief Bravo',
          approved_at: '2026-03-15T11:00:00Z',
        },
      ]);
    });
  });

  it('renders exact line-based row format logic and still filters by code and date', async () => {
    render(<OfficeORBApprovedEntriesPage />);

    await waitFor(() => {
      expect(screen.getByText('Alpha record')).toBeInTheDocument();
      expect(screen.getByText('Bravo record')).toBeInTheDocument();
    });

    expect(screen.getByText('Code (Letter)')).toBeInTheDocument();
    expect(screen.getByText('Item (Number)')).toBeInTheDocument();
    expect(
      screen.getByText('Record of operations / signature of officer in charge')
    ).toBeInTheDocument();

    const endPositionLine = `END POSITION 12\u00b015'N 079\u00b030'E`;
    const endPositionRow = screen.getByText(endPositionLine).closest('tr');
    expect(endPositionRow?.children[0]).toHaveTextContent('');
    expect(endPositionRow?.children[1]).toHaveTextContent('');
    expect(endPositionRow?.children[2]).toHaveTextContent('7');

    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('9.1')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();

    const signedRow = screen.getByText('SIGNED: Chief Officer').closest('tr');
    expect(signedRow?.children[2]).toHaveTextContent('');

    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'B' },
    });

    expect(screen.queryByText('Alpha record')).not.toBeInTheDocument();
    expect(screen.getByText('Bravo record')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('From date'), {
      target: { value: '2026-04-01' },
    });

    expect(screen.getByText('No approved entries found')).toBeInTheDocument();
  });
});
