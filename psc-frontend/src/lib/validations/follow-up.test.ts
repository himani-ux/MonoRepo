/**
 * Tests for Follow-up Validation Schemas
 */

import { describe, it, expect } from 'vitest';
import {
  followUpFormSchema,
  deficiencyUpdateSchema,
} from './follow-up';

function validFollowUp() {
  return {
    inspection_date: '2026-01-15',
    port_place: 'Singapore',
    country: 'SG',
    authority: 'MPA',
    inspector_name: 'John Smith',
    report_reference: 'REF-001',
    deficiency_updates: [],
  };
}

describe('followUpFormSchema — happy path', () => {
  it('test_feat_def_002_happy_path_valid_follow_up_passes', () => {
    const result = followUpFormSchema.safeParse(validFollowUp());
    expect(result.success).toBe(true);
  });

  it('test_feat_def_002_happy_path_minimal_follow_up_passes', () => {
    const result = followUpFormSchema.safeParse({
      inspection_date: '2026-01-15',
      port_place: 'Singapore',
    });
    expect(result.success).toBe(true);
  });

  it('test_feat_def_002_happy_path_with_deficiency_updates_passes', () => {
    const data = {
      ...validFollowUp(),
      deficiency_updates: [{ deficiency_id: 123, action_code_id: 10 }],
    };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(true);
  });
});

describe('followUpFormSchema — inspection_date validation', () => {
  it('test_feat_def_002_validation_future_date_passes', () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const data = { ...validFollowUp(), inspection_date: tomorrow.toISOString().split('T')[0] };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('test_feat_def_002_validation_missing_date_fails', () => {
    const data = { ...validFollowUp(), inspection_date: undefined };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it('test_feat_def_002_validation_empty_date_fails', () => {
    const data = { ...validFollowUp(), inspection_date: '' };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(false);
  });
});

describe('followUpFormSchema — port_place validation', () => {
  it('test_feat_def_002_validation_missing_port_fails', () => {
    const data = { ...validFollowUp(), port_place: undefined };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it('test_feat_def_002_validation_port_too_short_still_passes', () => {
    const data = { ...validFollowUp(), port_place: 'A' };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('test_feat_def_002_validation_port_over_max_still_passes', () => {
    const data = { ...validFollowUp(), port_place: 'A'.repeat(201) };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(true);
  });
});

describe('followUpFormSchema — optional field boundaries', () => {
  it('test_feat_def_002_validation_country_over_max_still_passes', () => {
    const data = { ...validFollowUp(), country: 'A'.repeat(101) };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('test_feat_def_002_validation_authority_over_max_still_passes', () => {
    const data = { ...validFollowUp(), authority: 'A'.repeat(201) };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('test_feat_def_002_validation_inspector_name_over_max_still_passes', () => {
    const data = { ...validFollowUp(), inspector_name: 'A'.repeat(201) };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('test_feat_def_002_validation_report_reference_over_max_still_passes', () => {
    const data = { ...validFollowUp(), report_reference: 'A'.repeat(101) };
    const result = followUpFormSchema.safeParse(data);
    expect(result.success).toBe(true);
  });
});

describe('deficiencyUpdateSchema', () => {
  it('test_feat_def_002_happy_path_valid_update_passes', () => {
    const result = deficiencyUpdateSchema.safeParse({
      deficiency_id: '123',
      action_code_id: 10,
    });
    expect(result.success).toBe(true);
  });

  it('test_feat_def_002_validation_numeric_deficiency_id_fails', () => {
    const result = deficiencyUpdateSchema.safeParse({
      deficiency_id: 123,
      action_code_id: 10,
    });
    expect(result.success).toBe(false);
  });

  it('test_feat_def_002_validation_missing_action_code_id_fails', () => {
    const result = deficiencyUpdateSchema.safeParse({
      deficiency_id: '123',
    });
    expect(result.success).toBe(false);
  });

  it('test_feat_def_002_validation_string_action_code_id_fails', () => {
    const result = deficiencyUpdateSchema.safeParse({
      deficiency_id: '123',
      action_code_id: 'not-a-number',
    });
    expect(result.success).toBe(false);
  });
});
