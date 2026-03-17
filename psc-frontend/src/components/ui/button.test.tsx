import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Button } from './button';

describe('Button', () => {
  it('renders as native button with default styling', () => {
    render(<Button>Save</Button>);
    const btn = screen.getByRole('button', { name: 'Save' });
    expect(btn.className).toContain('bg-primary-500');
  });

  it('supports asChild rendering while preserving classes', () => {
    render(
      <Button asChild variant="outline">
        <a href="/x">Go</a>
      </Button>
    );

    const link = screen.getByRole('link', { name: 'Go' });
    expect(link.className).toContain('border');
  });
});

