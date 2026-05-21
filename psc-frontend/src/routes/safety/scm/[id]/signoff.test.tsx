import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import SafetyScmSignoffRoute from './signoff';
import SafetyOverdueSoiBlockBanner from '@/components/safety/scm/overdue-soi-block-banner';

vi.mock('@/hooks/use-safety', () => ({
  safetyKeys: {
    scmMeeting: (id: number) => ['scm-meeting', id],
    scmMeetings: (filters: object) => ['scm-meetings', filters],
    scmSignoffPreflight: (id: number) => ['scm-preflight', id],
  },
  useSafetyScmMeeting: () => ({
    data: {
      id: 42,
      master_signed_off_at: null,
      sections: [
        {
          agenda_item_number: 2,
          decision: "",
          section_label: "Structured Review",
        },
      ],
      state: "SUBMITTED",
    },
    isError: false,
    isLoading: false,
  }),
  useSafetyScmSignoffPreflight: () => ({
    data: {
      agenda_complete: false,
      agenda_errors: ['Section 2 requires a decision/outcome.'],
      attendance_acknowledged: false,
      attendance_warnings_present: true,
      overdue_soi_areas: [],
    },
    isError: false,
    isLoading: false,
  }),
}));

vi.mock('@/lib/api/safety', () => ({
  safetyApi: {
    acknowledgeScmAttendance: vi.fn(),
    updateScmAgenda: vi.fn(),
    downloadScmPdf: vi.fn(),
    signoffScm: vi.fn(),
  },
}));

describe('SafetyScmSignoffRoute', () => {
  it('renders full sign-off preflight gates', () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/safety/scm/42/signoff']}>
          <Routes>
            <Route element={<SafetyScmSignoffRoute />} path="/safety/scm/:id/signoff" />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole('heading', { name: 'SCM Sign-Off' })).toBeInTheDocument();
    expect(screen.getByText('Attendance warnings require Master acknowledgement.')).toBeInTheDocument();
    expect(screen.getAllByText('Section 2 requires a decision/outcome.').length).toBeGreaterThan(0);
  });
});

describe('SafetyOverdueSoiBlockBanner', () => {
  it('renders the hard block state when overdue areas exist', () => {
    render(
      <SafetyOverdueSoiBlockBanner
        overdueAreas={[
          {
            area_id: 3,
            area_name: 'Navigating Bridge & Monkey Island',
            due_at: '2026-04-23T08:00:00+05:30',
            message: 'Area 3 overdue by 5 days',
            overdue_days: 5,
          },
        ]}
      />
    );

    expect(screen.getByText('Overdue SOI hard block')).toBeInTheDocument();
    expect(screen.getByText('Area 3 overdue by 5 days')).toBeInTheDocument();
  });
});
