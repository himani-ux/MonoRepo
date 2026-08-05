import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const phase9Mocks = vi.hoisted(() => ({
  downloadIncidentMscMepc3: vi.fn(),
  downloadIncidentPdf: vi.fn(),
  getIncidentClosureSummary: vi.fn(),
}));

vi.mock('../../../hooks/use-auth', () => ({
  useAuth: () => ({
    hasProcess: () => false,
    role: 'VESSEL_MASTER',
    user: {
      role: 'VESSEL_MASTER',
      safety_role_name: 'MASTER',
    },
  }),
}));

vi.mock('../../../lib/api/safety', () => ({
  safetyApi: {
    downloadIncidentMscMepc3: phase9Mocks.downloadIncidentMscMepc3,
    downloadIncidentPdf: phase9Mocks.downloadIncidentPdf,
    getIncidentClosureSummary: phase9Mocks.getIncidentClosureSummary,
  },
}));

vi.mock('./incident-pdf-section-selector', () => ({
  DEFAULT_INCIDENT_PDF_SECTION_KEYS: ['summary'],
  IncidentPdfSectionSelector: () => <div data-testid="pdf-section-selector" />,
}));

import { SafetyIncidentPhase9 } from './phase-9-workspace';

describe('SafetyIncidentPhase9', () => {
  beforeEach(() => {
    phase9Mocks.getIncidentClosureSummary.mockResolvedValue({
      audit_summary: {
        field_history_count: 3,
        latest_field_change: null,
        latest_phase_log: null,
        phase_log_count: 2,
      },
      exports: {
        incident_pdf: { available: true, endpoint: '/pdf' },
        msc_mepc3: { available: true, endpoint: '/msc' },
      },
      field_history: [
        {
          actor_role_code: 'MASTER',
          actor_user_id: 'master-1',
          change_reason: null,
          changed_at: '2026-06-29T08:30:00Z',
          field_name: 'risk_band',
          id: 9,
          new_value: 'YELLOW',
          old_value: 'GREEN',
        },
      ],
      incident: {
        closed_at: '2026-06-29T09:00:00Z',
        closure_reason: 'All checks completed.',
        current_phase: 9,
        dpa_accepted_at: '2026-06-29T08:45:00Z',
        dpa_accepted_by: 'dpa-1',
        fm_approved_at: null,
        fm_approved_by: null,
        id: 123,
        imo_classifier: 'NOT_APPLICABLE',
        incident_number: 'ARY/2026/003',
        narrative: 'Closed incident narrative.',
        occurred_at: '2026-06-28T10:00:00Z',
        record_type: 'INCIDENT',
        reported_at: '2026-06-28T10:30:00Z',
        risk_band: 'YELLOW',
        state: 'CLOSED',
        vessel_id: '7',
        vessel_name: 'ARYA',
      },
      phase_logs: [
        {
          actor_role_code: 'MASTER',
          actor_user_id: 'master-1',
          id: 1,
          loop_back_reason: null,
          occurred_at: '2026-06-28T10:30:00Z',
          phase_from: null,
          phase_to: 1,
          transition_type: 'FORWARD',
        },
        {
          actor_role_code: 'DPA',
          actor_user_id: 'dpa-1',
          id: 2,
          loop_back_reason: null,
          occurred_at: '2026-06-29T08:45:00Z',
          phase_from: 1,
          phase_to: 3,
          transition_type: 'FORWARD',
        },
      ],
      signature_chain: {
        dpa: { present: true, required: true },
        fm: { present: false, required: false },
      },
    });
  });

  it('shows a simplified final record without change-history or raw classifier values', async () => {
    render(
      <MemoryRouter initialEntries={['/safety/incidents/123/phase-7']}>
        <Routes>
          <Route path="/safety/incidents/:id/phase-7" element={<SafetyIncidentPhase9 />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Incident Details')).toBeTruthy();
    });

    expect(screen.queryByText('Change History')).toBeNull();
    expect(screen.queryByText('History Rows')).toBeNull();
    expect(screen.queryByText('NOT_APPLICABLE')).toBeNull();
    expect(screen.getByText('IMO class: No IMO class')).toBeTruthy();
    expect(screen.getByText('Medium')).toBeTruthy();
    expect(screen.getByText('A simple timeline of how the incident moved through the workflow.')).toBeTruthy();
    expect(screen.getByText('Moved from Phase 1 - Report Incident to Phase 2 - RCA (Root Cause Analysis).')).toBeTruthy();
  });
});
