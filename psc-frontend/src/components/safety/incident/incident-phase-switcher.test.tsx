import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import {
  displayIncidentPhase,
  incidentPhaseLabel,
} from '../../../lib/safety/incident-phase-display';
import IncidentPhaseSwitcher from './incident-phase-switcher';

describe('IncidentPhaseSwitcher', () => {
  it('shows the current incident workflow as a clean sequential phase list', () => {
    render(
      <MemoryRouter initialEntries={['/safety/incidents/incident-1/phase-5']}>
        <Routes>
          <Route path="/safety/incidents/:id/phase-5" element={<IncidentPhaseSwitcher />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: /Phase 5Add EvidenceDocuments/i })).toHaveAttribute(
      'href',
      '/safety/incidents/incident-1/phase-4/paper',
    );
    expect(screen.getByRole('link', { name: /Phase 6Office ReviewApprove or return/i })).toHaveAttribute(
      'href',
      '/safety/incidents/incident-1/phase-5',
    );
    expect(screen.getByRole('link', { name: /Phase 7Loss EvaluationAssess loss and cost/i })).toHaveAttribute(
      'href',
      '/safety/incidents/incident-1/phase-6',
    );
    expect(screen.queryByText('Phase 8')).toBeNull();
  });

  it('maps legacy backend phase values to sequential visible labels', () => {
    expect(displayIncidentPhase(4)).toBe(5);
    expect(incidentPhaseLabel(4)).toBe('Phase 5 - Add Evidence');
    expect(displayIncidentPhase(7)).toBe(6);
    expect(incidentPhaseLabel(7)).toBe('Phase 6 - Office Review');
    expect(displayIncidentPhase(8)).toBe(7);
    expect(incidentPhaseLabel(8)).toBe('Phase 7 - Loss Evaluation');
  });
});
