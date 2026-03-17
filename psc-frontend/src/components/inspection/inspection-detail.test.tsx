/**
 * Tests for FEAT-INS-011: View Inspection Detail
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-011
 * Flow Reference: Docs/APP_FLOW.md Section 2.2 (Inspection Detail)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const inspectionDetailMocks = vi.hoisted(() => ({
  onAddDeficiency: vi.fn(),
  onDeficiencyClick: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
}));

vi.mock('./deficiency-list', () => ({
  DeficiencyList: (props: any) => (
    <div data-testid="deficiency-list-mock">
      <div>Deficiency Count: {props.deficiencies.length}</div>
      <button type="button" onClick={props.onAddDeficiency}>
        Trigger Add
      </button>
      <button
        type="button"
        onClick={() => props.onDeficiencyClick?.(props.deficiencies[0])}
      >
        Trigger Click
      </button>
    </div>
  ),
}));

import { InspectionDetail } from './inspection-detail';

function buildInspection(overrides: Record<string, unknown> = {}) {
  return {
    id: 1001,
    vessel_id: 1,
    vessel_name: 'MV Atlas',
    inspection_type: 'PSC',
    psc_subtype: 'INITIAL',
    inspection_date: '2026-02-01',
    port: 'Singapore',
    port_state: 'SG',
    mou_code: 'TOKYO',
    inspector_name: 'John Inspector',
    is_detention: true,
    detention_reason: 'Detained due to fire-safety deficiency',
    status: 'SUBMITTED',
    report_file: null,
    deficiency_count: 1,
    created_by: 1,
    created_at: '2026-02-01T08:00:00Z',
    updated_at: '2026-02-01T08:00:00Z',
    submitted_at: '2026-02-01T10:00:00Z',
    pic_reviewed_at: null,
    dpa_closed_at: null,
    imo_number: '1234567',
    authority: 'MPA Singapore',
    report_reference: 'PSC-2026-001',
    pic_review_comments: null,
    dpa_close_comments: null,
    parent_inspection_id: null,
    reports: [
      {
        id: 1,
        file_name: 'inspection_report.pdf',
        file_path: '/uploads/inspection_report.pdf',
        uploaded_by: 1,
        uploaded_by_name: 'Master User',
        uploaded_at: '2026-02-01T09:00:00Z',
      },
    ],
    deficiencies: [
      {
        id: 501,
        def_code: '10101',
        def_code_description: 'Certificate',
        description: 'Certificate expired',
        action_code: '30',
        action_code_description: 'Rectify',
        target_date: '2026-02-05',
        is_cleared: false,
        car: { id: 7001, car_number: 'PSC-2026-001', status: 'DRAFT' },
        created_at: '2026-02-01T08:30:00Z',
        updated_at: '2026-02-01T08:30:00Z',
      },
    ],
    activity_history: [
      {
        id: 9001,
        entity_type: 'INSPECTION',
        entity_id: 1001,
        event_type: 'INSPECTION_SUBMITTED',
        event_description: 'Inspection submitted for review',
        performed_by: 'master01',
        performed_by_name: 'Master User',
        performed_at: '2026-02-01T10:00:00Z',
        metadata: {},
      },
    ],
    ...overrides,
  } as any;
}

describe('InspectionDetail', () => {
  it('test_feat_ins_011_happy_path_renders_header_fields_and_detention_banner', () => {
    render(<InspectionDetail inspection={buildInspection()} />);

    expect(screen.getByText('MV Atlas')).toBeInTheDocument();
    expect(screen.getByText('IMO: 1234567')).toBeInTheDocument();
    expect(screen.getByText('PSC - Initial')).toBeInTheDocument();
    expect(screen.getByText('DETENTION')).toBeInTheDocument();
    expect(screen.getByText('Detained due to fire-safety deficiency')).toBeInTheDocument();
  });

  it('test_feat_ins_011_report_section_shows_primary_report_links_and_uploader', () => {
    render(<InspectionDetail inspection={buildInspection()} />);

    expect(screen.getByText('inspection_report.pdf')).toBeInTheDocument();
    expect(screen.getByText(/Uploaded:/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /view/i }).getAttribute('href')).toContain(
      '/uploads/inspection_report.pdf'
    );
  });

  it('test_feat_ins_011_deficiency_list_receives_data_and_triggers_callbacks', () => {
    render(
      <InspectionDetail
        inspection={buildInspection()}
        onAddDeficiency={inspectionDetailMocks.onAddDeficiency}
        onDeficiencyClick={inspectionDetailMocks.onDeficiencyClick}
      />
    );

    expect(screen.getByText('Deficiency Count: 1')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Trigger Add' }));
    expect(inspectionDetailMocks.onAddDeficiency).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Trigger Click' }));
    expect(inspectionDetailMocks.onDeficiencyClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: 501, def_code: '10101' })
    );
  });

  it('test_feat_ins_011_activity_history_expands_and_shows_event_rows', () => {
    render(<InspectionDetail inspection={buildInspection()} />);

    expect(screen.queryByText('Inspection submitted for review')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /activity history/i }));
    expect(screen.getByText('Inspection submitted for review')).toBeInTheDocument();
  });

  it('test_feat_ins_011_activity_history_empty_state_shows_message_when_expanded', () => {
    render(<InspectionDetail inspection={buildInspection({ activity_history: [] })} />);

    fireEvent.click(screen.getByRole('button', { name: /activity history/i }));
    expect(screen.getByText('No activity recorded yet')).toBeInTheDocument();
  });
});
