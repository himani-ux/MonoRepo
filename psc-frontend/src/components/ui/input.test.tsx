import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Input } from './input';

describe('Input', () => {
  it('applies error styling when error prop is true', () => {
    render(<Input aria-label="name" error />);
    const input = screen.getByRole('textbox', { name: 'name' });
    expect(input.className).toContain('border-error-500');
  });

  it('supports disabled state', () => {
    render(<Input aria-label="email" disabled />);
    expect(screen.getByRole('textbox', { name: 'email' })).toBeDisabled();
  });
});

