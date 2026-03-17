/**
 * Tests for FEAT-NOTIF-001 notification badge count display.
 *
 * PRD Reference: Docs/PRD.md Section 2.7 - FEAT-NOTIF-001
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { NotificationBadge } from './notification-badge';

describe('NotificationBadge', () => {
  it('test_feat_notif_001_hides_badge_when_count_is_zero_or_negative', () => {
    const { rerender } = render(<NotificationBadge count={0} />);
    expect(document.body.textContent?.trim()).toBe('');

    rerender(<NotificationBadge count={-1} />);
    expect(document.body.textContent?.trim()).toBe('');
  });

  it('test_feat_notif_001_shows_exact_count_when_between_1_and_99', () => {
    render(<NotificationBadge count={7} />);
    expect(screen.getByText('7')).toBeInTheDocument();
  });

  it('test_feat_notif_001_caps_display_value_to_99_plus_for_large_count', () => {
    render(<NotificationBadge count={120} />);
    expect(screen.getByText('99+')).toBeInTheDocument();
  });
});

