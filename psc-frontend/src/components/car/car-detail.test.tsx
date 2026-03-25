/**
 * Tests for FEAT-CAR-010: View CAR Detail
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-010
 * Flow Reference: Docs/APP_FLOW.md Section 2.3 (CAR Detail)
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const carDetailMocks = vi.hoisted(() => ({
  onUploadEvidence: vi.fn(),
}));

vi.mock('./root-cause-section', () => ({
  RootCauseSection: ({ rootCauseSummary, clcItems }: any) => (
    <div data-testid="root-cause-section">
      RootCause:{rootCauseSummary ?? 'none'} CLC:{clcItems.length}
    </div>
  ),
}));

vi.mock('./corrective-action-list', () => ({
  CorrectiveActionList: ({ actions }: any) => (
    <div data-testid="corrective-action-list">Actions:{actions.length}</div>
  ),
}));

vi.mock('./evidence-section', () => ({
  EvidenceSection: ({ evidence, onUpload }: any) => (
    <div data-testid="evidence-section">
      Evidence:{evidence.length}
      <button type="button" onClick={onUpload}>
        Upload Trigger
      </button>
    </div>
  ),
}));

vi.mock('./activity-history', () => ({
  ActivityHistory: ({ events }: any) => (
    <div data-testid="activity-history">Events:{events.length}</div>
  ),
}));

vi.mock('./audit-log', () => ({
  AuditLog: ({ entries }: any) => (
    <div data-testid="audit-log">Audit:{entries.length}</div>
  ),
}));

import { CARDetail } from './car-detail';

function buildCar(overrides: Record<string, unknown> = {}) {
  return {
    id: 3001,
    car_number: 'PSC-2026-001',
    status: 'DRAFT',
    status_display: 'Draft',
    root_cause_summary: 'Root cause summary content for validation and display.',
    target_date: '2026-02-10',
    pic_comment: null,
    pic_accepted_by: null,
    pic_accepted_at: null,
    rework_reason: null,
    rework_requested_by: null,
    rework_requested_at: null,
    rework_count: 0,
    dpa_comment: null,
    dpa_closed_by: null,
    dpa_closed_at: null,
    created_by: 'master01',
    created_date: '2026-02-01T08:00:00Z',
    updated_by: null,
    updated_date: null,
    deficiency: {
      id: 'def-1',
      def_code: '10101',
      def_code_id: 'dc-1',
      description: 'Expired certificate',
      action_code: '30',
      action_code_id: 30,
      target_date: '2026-02-07',
      is_cleared: false,
      cleared_date: null,
    },
    inspection: {
      id: 'ins-1',
      inspection_type: 'PSC',
      psc_subtype: 'INITIAL',
      inspection_date: '2026-02-01',
      port_place: 'Singapore',
      vessel_id: 'v-1',
      vessel_name: 'MV Atlas',
    },
    clc_items: [{ id: 1, clc_item_id: 'CLC001', custom_cause_text: '' }],
    corrective_actions: [],
    evidence: [],
    physical_verification: null,
    activity_history: [
      {
        id: 1,
        entity_type: 'CAR',
        entity_id: 3001,
        event_type: 'CAR_CREATED',
        event_description: 'CAR created',
        performed_by: 'master01',
        performed_by_name: 'Master User',
        performed_at: '2026-02-01T08:00:00Z',
        metadata: {},
      },
    ],
    audit_log: [],
    ...overrides,
  } as any;
}

describe('CARDetail', () => {
  beforeEach(() => {
    carDetailMocks.onUploadEvidence.mockReset();
  });

  it('test_feat_car_010_happy_path_renders_core_header_and_deficiency_fields', () => {
    render(<CARDetail car={buildCar()} />);

    expect(screen.getByText('PSC-2026-001')).toBeInTheDocument();
    expect(screen.getByText('10101')).toBeInTheDocument();
    expect(screen.getByText('Expired certificate')).toBeInTheDocument();
    expect(screen.getByText('MV Atlas')).toBeInTheDocument();
  });

  it('test_feat_car_010_rework_banner_renders_reason_and_count_for_reworked_status', () => {
    render(
      <CARDetail
        car={buildCar({
          status: 'RETURNED_FOR_REWORK',
          rework_reason: 'Evidence unclear; please upload clearer photos.',
          rework_count: 2,
        })}
      />
    );

    expect(screen.getByText('Rework Requested (#2)')).toBeInTheDocument();
    expect(screen.getByText('Evidence unclear; please upload clearer photos.')).toBeInTheDocument();
  });

  it('test_feat_car_010_evidence_section_exposes_upload_action_callback', () => {
    render(
      <CARDetail
        car={buildCar()}
        onUploadEvidence={carDetailMocks.onUploadEvidence}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Upload Trigger' }));
    expect(carDetailMocks.onUploadEvidence).toHaveBeenCalledTimes(1);
  });

  it('test_feat_car_010_shows_audit_log_only_for_office_or_dpa_when_entries_exist', () => {
    const withAudit = buildCar({
      audit_log: [
        {
          id: 11,
          entity_type: 'CAR',
          entity_id: 3001,
          action: 'UPDATE',
          field_name: 'target_date',
          old_value: '2026-02-05',
          new_value: '2026-02-10',
          performed_by: 'office01',
          performed_by_role: 'OFFICE_PIC',
          performed_at: '2026-02-02T10:00:00Z',
          is_office_edit_assist: false,
        },
      ],
    });

    const { rerender } = render(<CARDetail car={withAudit} isOfficeOrDPA />);
    expect(screen.getByTestId('audit-log')).toHaveTextContent('Audit:1');

    rerender(<CARDetail car={withAudit} isOfficeOrDPA={false} />);
    expect(screen.queryByTestId('audit-log')).not.toBeInTheDocument();
  });

  it('test_feat_car_010_renders_pic_and_dpa_comments_when_present', () => {
    const picComment = 'PIC validated corrective actions and attached the full closure narrative for report rendering.';
    const dpaComment = 'DPA final closure approved with all supporting evidence reviewed.';

    render(
      <CARDetail
        car={buildCar({
          pic_comment: picComment,
          dpa_comment: dpaComment,
        })}
      />
    );

    const picCommentNode = screen.getByText(picComment);
    const dpaCommentNode = screen.getByText(dpaComment);

    expect(screen.getByText('PIC Comment:')).toBeInTheDocument();
    expect(picCommentNode).toBeInTheDocument();
    expect(picCommentNode).toHaveClass('whitespace-pre-wrap', 'break-words');
    expect(screen.getByText('DPA Comment:')).toBeInTheDocument();
    expect(dpaCommentNode).toBeInTheDocument();
    expect(dpaCommentNode).toHaveClass('whitespace-pre-wrap', 'break-words');
  });
});