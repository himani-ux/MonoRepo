/**
 * Tests for status badge mapping and indicator behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-010
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-009
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { StatusBadge } from './status-badge';

describe('StatusBadge', () => {
  it('test_feat_ins_010_displays_default_mapped_label_for_status', () => {
    render(<StatusBadge status="DRAFT" />);
    expect(screen.getByText(/DRAFT/i)).toBeInTheDocument();
  });

  it('test_feat_car_009_custom_label_overrides_default_label', () => {
    render(<StatusBadge status="SUBMITTED" label="Custom Submitted" />);
    expect(screen.getByText('Custom Submitted')).toBeInTheDocument();
  });

  it('test_feat_ins_010_indicator_dot_renders_for_detention_when_enabled', () => {
    const { container } = render(
      <StatusBadge status="DETENTION" showIndicator />
    );
    expect(container.querySelector('.rounded-full.bg-current')).not.toBeNull();
  });
});

