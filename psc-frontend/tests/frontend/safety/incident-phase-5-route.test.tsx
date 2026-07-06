import type { ReactNode } from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useRoutes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { SafetyAuthProvider } from '../../../src/hooks/safety/use-auth';
import { safetyRoutes } from '../../../src/routes/safety';
import { useAuthStore } from '../../../src/stores/auth-store';

const safetyApiMocks = vi.hoisted(() => ({
  getIncidentPhase7Preflight: vi.fn(),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: ReactNode }) => (
    <div data-testid="root-layout">{children}</div>
  ),
}));

vi.mock('../../../src/lib/api/safety', async () => {
  const actual = await vi.importActual<
    typeof import('../../../src/lib/api/safety')
  >('../../../src/lib/api/safety');
  return {
    ...actual,
    safetyApi: {
      ...actual.safetyApi,
      getIncidentPhase7Preflight: safetyApiMocks.getIncidentPhase7Preflight,
    },
  };
});

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

describe('Safety Office Review route', () => {
  it('renders Office Review on the current phase-5 path', async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      tokens: null,
      user: {
        form_ids: ['SAF_F_001'],
        full_name: 'dpa-1',
        id: 'dpa-1',
        process_ids: ['SAF_P_006'],
        role: 'DPA',
        username: 'dpa-1',
        vessel_id: null,
      } as never,
    });
    safetyApiMocks.getIncidentPhase7Preflight.mockResolvedValue({
      blockers: [],
      closer_role: 'DPA',
      current_phase: 7,
      generated_at: '2026-07-03T00:00:00Z',
      incident_id: 42,
      office_comment: 'Office note already saved.',
      pdf_preview: {
        available: true,
        download_path: '/api/safety/export/incident/42/pdf/',
        expected_sections: 8,
        incident_id: 42,
        message: 'PDF ready.',
        status: 'READY',
      },
      ready_for_acceptance: true,
      recommendation_tier_count: {
        CORRECTIVE: 1,
        PREVENTIVE: 1,
      },
      required_process_id: 'SAF_P_004',
      risk_band: 'YELLOW',
      root_count: 1,
      signature_chain_status: {
        dpa: { present: false, required: true },
        fm: { present: false, required: false },
        hod: { present: true, required: true },
        master: { present: true, required: true },
        pic: { present: false, required: false },
        reporter: { present: true, required: true },
      },
    });
    render(
      <MemoryRouter initialEntries={['/safety/incidents/42/phase-5']}>
        <SafetyAuthProvider value={{ formIds: ['SAF_F_001'] }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>
    );

    const officeComments = await screen.findByLabelText(
      'Office Comments/lesson learnt',
      {},
      { timeout: 7000 }
    );
    expect(officeComments).toHaveValue('Office note already saved.');
    expect(screen.getByText('Office Review')).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Phase 5 Causal Analysis' })
    ).not.toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase7Preflight).toHaveBeenCalledWith(
      '42'
    );
  });
});
