import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiClientMock = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('./client', () => ({
  apiClient: apiClientMock,
}));

vi.mock('@/lib/utils/constants', () => ({
  API_BASE_URL: 'http://localhost:8000',
}));

import { safetyApi } from './safety';

describe('safetyApi incident endpoints', () => {
  beforeEach(() => {
    apiClientMock.get.mockReset();
  });

  it('uses the Phase 7 preflight endpoint for office review readiness', async () => {
    apiClientMock.get.mockResolvedValue({ data: { current_phase: 8 } });

    await safetyApi.getIncidentPhase7Preflight('incident-1');

    expect(apiClientMock.get).toHaveBeenCalledWith(
      'http://localhost:8000/api/safety/incidents/incident-1/phase-7/preflight/',
    );
  });
});
