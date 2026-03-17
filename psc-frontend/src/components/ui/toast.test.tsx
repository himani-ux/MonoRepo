import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  ToastProvider,
  ToastViewport,
  Toast,
  ToastTitle,
  ToastDescription,
  ToastClose,
} from './toast';

describe('Toast', () => {
  it('renders toast title, description, and close action', () => {
    render(
      <ToastProvider>
        <Toast open variant="success">
          <div>
            <ToastTitle>Saved</ToastTitle>
            <ToastDescription>Record updated</ToastDescription>
          </div>
          <ToastClose />
        </Toast>
        <ToastViewport />
      </ToastProvider>
    );

    expect(screen.getByText('Saved')).toBeInTheDocument();
    expect(screen.getByText('Record updated')).toBeInTheDocument();
  });
});

