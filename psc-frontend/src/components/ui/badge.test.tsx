import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Badge } from './badge';

describe('Badge', () => {
  it('renders content with requested variant classes', () => {
    render(<Badge variant="submitted">Submitted</Badge>);
    const badge = screen.getByText('Submitted');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-primary-100');
  });
});

