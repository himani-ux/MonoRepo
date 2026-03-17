import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Checkbox } from './checkbox';

describe('Checkbox', () => {
  it('toggles checked state when clicked', () => {
    render(<Checkbox aria-label="agree" />);
    const checkbox = screen.getByRole('checkbox', { name: 'agree' });

    expect(checkbox).toHaveAttribute('aria-checked', 'false');
    fireEvent.click(checkbox);
    expect(checkbox).toHaveAttribute('aria-checked', 'true');
  });
});

