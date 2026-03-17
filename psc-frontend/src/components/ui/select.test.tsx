import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from './select';

describe('Select', () => {
  it('renders trigger and applies error class when requested', () => {
    render(
      <Select>
        <SelectTrigger error aria-label="Type select">
          <SelectValue placeholder="Pick one" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="A">A</SelectItem>
        </SelectContent>
      </Select>
    );

    const trigger = screen.getByRole('combobox', { name: 'Type select' });
    expect(trigger.className).toContain('border-error-500');
  });
});

