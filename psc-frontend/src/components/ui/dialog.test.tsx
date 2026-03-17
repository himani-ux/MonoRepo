import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './dialog';

describe('Dialog', () => {
  it('renders open dialog content with title and description', () => {
    render(
      <Dialog open>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Action</DialogTitle>
            <DialogDescription>Proceed?</DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );

    expect(screen.getByText('Confirm Action')).toBeInTheDocument();
    expect(screen.getByText('Proceed?')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });
});

