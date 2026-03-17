import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Skeleton } from './skeleton';

describe('Skeleton', () => {
  it('renders with animate-pulse default class', () => {
    const { container } = render(<Skeleton className="h-4 w-8" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain('animate-pulse');
    expect(el.className).toContain('h-4');
  });
});

