/**
 * Regression coverage for unified CAR workflow actions.
 *
 * The backend requires comments for DPA close and rework-style workflow
 * actions, so the client must not post an empty workflow payload.
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const carWorkflowMocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useCARAvailableActions: vi.fn(),
  useCAR: vi.fn(),
  useTransitionCAR: vi.fn(),
  mutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => carWorkflowMocks.useAuth(),
}));

vi.mock('@/hooks/use-cars', () => ({
  useCARAvailableActions: (carId: string | number) =>
    carWorkflowMocks.useCARAvailableActions(carId),
  useCAR: (carId: string | number) => carWorkflowMocks.useCAR(carId),
  useTransitionCAR: (carId: string | number) =>
    carWorkflowMocks.useTransitionCAR(carId),
}));

import { CARWorkflowActions } from './car-workflow-actions';

function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
}

describe('CARWorkflowActions', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    carWorkflowMocks.useAuth.mockReturnValue({ role: 'DPA' });
    carWorkflowMocks.useCARAvailableActions.mockReturnValue({
      data: [
        {
          action: 'CLOSE_CAR',
          label: 'Close CAR',
          comment_required: false,
        },
      ],
    });
    carWorkflowMocks.useCAR.mockReturnValue({
      data: {
        status: 'SUBMITTED_TO_DPA',
        clc_items: [],
        corrective_actions: [],
        evidence: [],
      },
    });
    carWorkflowMocks.mutateAsync.mockResolvedValue({
      id: 'car-1',
      status: 'CLOSED',
      action: 'CLOSE_CAR',
    });
    carWorkflowMocks.useTransitionCAR.mockReturnValue({
      mutateAsync: carWorkflowMocks.mutateAsync,
      isPending: false,
    });
  });

  it('requires a DPA close comment even when available-actions metadata is stale', async () => {
    renderWithQueryClient(<CARWorkflowActions carId="car-1" />);

    fireEvent.click(screen.getByRole('button', { name: 'Close CAR' }));

    const confirmButton = screen.getByRole('button', { name: 'Confirm' });
    expect(confirmButton).toBeDisabled();

    fireEvent.click(confirmButton);
    expect(carWorkflowMocks.mutateAsync).not.toHaveBeenCalled();

    fireEvent.change(screen.getByPlaceholderText('Enter your comment (required)...'), {
      target: { value: '  DPA reviewed the completed corrective actions.  ' },
    });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(carWorkflowMocks.mutateAsync).toHaveBeenCalledWith({
        action: 'CLOSE_CAR',
        comment: 'DPA reviewed the completed corrective actions.',
      });
    });
  });
});
