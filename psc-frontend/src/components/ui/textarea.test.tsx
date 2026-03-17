import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Textarea } from './textarea';

describe('Textarea', () => {
  it('applies error style when error prop is true', () => {
    render(<Textarea aria-label="remarks" error />);
    const area = screen.getByRole('textbox', { name: 'remarks' });
    expect(area.className).toContain('border-error-500');
  });

  it('supports disabled state', () => {
    render(<Textarea aria-label="notes" disabled />);
    expect(screen.getByRole('textbox', { name: 'notes' })).toBeDisabled();
  });
});

