import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './dropdown-menu';

describe('DropdownMenu', () => {
  it('renders open dropdown content and menu item', () => {
    render(
      <DropdownMenu open>
        <DropdownMenuTrigger>Open</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Sign out</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );

    expect(screen.getByText('Sign out')).toBeInTheDocument();
  });
});

