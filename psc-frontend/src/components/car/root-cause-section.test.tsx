/**
 * Tests for FEAT-CAR-002 root cause section rendering.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-002
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { RootCauseSection } from './root-cause-section';

describe('RootCauseSection', () => {
  it('test_feat_car_002_empty_state_shows_placeholder_when_no_summary_or_clc', () => {
    render(<RootCauseSection rootCauseSummary={null} clcItems={[]} />);
    expect(
      screen.getByText('No root cause analysis provided yet')
    ).toBeInTheDocument();
  });

  it('test_feat_car_002_displays_clc_codes_and_custom_cause_text', () => {
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
    expect(screen.getByText('CLC001')).toBeInTheDocument();
    expect(screen.getByText('CLC002')).toBeInTheDocument();
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

