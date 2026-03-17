/**
 * Tests for FEAT-CAR-002 root cause section rendering.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-002
 */

import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const rootCauseSectionMocks = vi.hoisted(() => ({
  useCLCItems: vi.fn(),
}));

vi.mock('@/hooks/use-masters', () => ({
  useCLCItems: () => rootCauseSectionMocks.useCLCItems(),
}));

import { RootCauseSection } from './root-cause-section';

describe('RootCauseSection', () => {
  beforeEach(() => {
    rootCauseSectionMocks.useCLCItems.mockReset();
    rootCauseSectionMocks.useCLCItems.mockReturnValue({ data: [] });
  });

  it('test_feat_car_002_empty_state_shows_placeholder_when_no_summary_or_clc', () => {
    render(<RootCauseSection rootCauseSummary={null} clcItems={[]} />);
    expect(
      screen.getByText('No root cause analysis provided yet')
    ).toBeInTheDocument();
  });

  it('test_feat_car_002_displays_clc_code_with_description_and_custom_cause_text', () => {
    rootCauseSectionMocks.useCLCItems.mockReturnValue({
      data: [
        {
          clc_code: 'CLC001',
          item_name: 'Leadership gap',
          item_description: null,
          category_id: 1,
          category_code: '1',
          category_name: 'Following Procedures',
          category_type: 'ROOT',
          display_text: 'CLC001 - Leadership gap',
          sort_order: 1,
        },
        {
          clc_code: 'CLC002',
          item_name: 'Training breakdown',
          item_description: null,
          category_id: 2,
          category_code: '2',
          category_name: 'Training',
          category_type: 'ROOT',
          display_text: 'CLC002 - Training breakdown',
          sort_order: 2,
        },
      ],
    });

    render(
      <RootCauseSection
        rootCauseSummary={null}
        clcItems={
          [
            { id: '1', clc_item_id: 'CLC001', custom_cause_text: 'Lack of training' },
            { id: '2', clc_item_id: 'CLC002' },
          ] as any
        }
      />
    );

    expect(screen.getByText('CLC Codes:')).toBeInTheDocument();
    expect(screen.getByText('CLC001 - Leadership gap')).toBeInTheDocument();
    expect(screen.getByText('CLC002 - Training breakdown')).toBeInTheDocument();
    expect(screen.getByText(': Lack of training')).toBeInTheDocument();
  });

  it('test_feat_car_002_displays_summary_text_when_present', () => {
    render(
      <RootCauseSection
        rootCauseSummary="Root cause traced to missing maintenance checklist sign-off."
        clcItems={[]}
      />
    );

    expect(screen.getByText('Summary:')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Root cause traced to missing maintenance checklist sign-off.'
      )
    ).toBeInTheDocument();
  });
});