import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Label } from './label';

describe('Label', () => {
  it('renders text and htmlFor binding', () => {
    render(<Label htmlFor="field-id">Field Label</Label>);
    const label = screen.getByText('Field Label');
    expect(label).toHaveAttribute('for', 'field-id');
  });
});

