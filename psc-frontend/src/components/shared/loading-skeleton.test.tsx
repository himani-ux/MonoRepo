/**
 * Tests for loading skeleton variants.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-010
 */

import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  TextSkeleton,
  ListSkeleton,
  FormSkeleton,
  DetailHeaderSkeleton,
} from './loading-skeleton';

describe('LoadingSkeleton', () => {
  it('test_feat_ins_010_text_skeleton_applies_width_variant_class', () => {
    const { container } = render(<TextSkeleton width="1/2" />);
    expect(container.querySelector('.w-1\\/2')).not.toBeNull();
  });

  it('test_feat_ins_010_list_skeleton_renders_requested_item_count', () => {
    const { container } = render(<ListSkeleton count={4} />);
    expect(container.querySelectorAll('.rounded-lg.border').length).toBe(4);
  });

  it('test_feat_ins_010_form_skeleton_renders_configured_field_count', () => {
    const { container } = render(<FormSkeleton fieldCount={3} />);
    expect(container.querySelectorAll('.h-10.w-full').length).toBe(3);
  });

  it('test_feat_ins_010_detail_header_skeleton_renders_header_blocks', () => {
    const { container } = render(<DetailHeaderSkeleton />);
    expect(container.querySelectorAll('.h-6').length).toBeGreaterThanOrEqual(1);
  });
});

