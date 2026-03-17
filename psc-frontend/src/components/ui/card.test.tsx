import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from './card';

describe('Card', () => {
  it('applies clickable and detention visual classes', () => {
    render(
      <Card clickable detention>
        <span>Body</span>
      </Card>
    );

    const body = screen.getByText('Body').closest('div');
    expect(body?.className).toContain('cursor-pointer');
    expect(body?.className).toContain('border-l-error-500');
  });

  it('renders header/content/footer composition', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>Card Description</CardDescription>
        </CardHeader>
        <CardContent>Card Content</CardContent>
        <CardFooter>Card Footer</CardFooter>
      </Card>
    );

    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card Description')).toBeInTheDocument();
    expect(screen.getByText('Card Content')).toBeInTheDocument();
    expect(screen.getByText('Card Footer')).toBeInTheDocument();
  });
});

