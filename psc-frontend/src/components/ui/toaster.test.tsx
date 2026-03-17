import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const toasterMocks = vi.hoisted(() => ({
  useToast: vi.fn(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => toasterMocks.useToast(),
}));

import { Toaster } from './toaster';

describe('Toaster', () => {
  it('renders active toasts from toast store', () => {
    toasterMocks.useToast.mockReturnValue({
      toasts: [
        {
          id: '1',
          open: true,
          title: 'Saved',
          description: 'Changes were saved',
        },
      ],
    });

    render(<Toaster />);

    expect(screen.getByText('Saved')).toBeInTheDocument();
    expect(screen.getByText('Changes were saved')).toBeInTheDocument();
  });
});

