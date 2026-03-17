/**
 * Tests for FEAT-SYNC-006: Attachment Upload Retry
 *
 * PRD Reference: Docs/PRD.md Section 2.6 - FEAT-SYNC-006
 * Validation Reference: Docs/VALIDATION_RULES.md Section 11.4
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { AttachmentUploadURL } from '@/lib/api/sync';
import {
  clearPendingFiles,
  getPendingFileCount,
  registerFileForUpload,
  uploadAttachments,
} from './attachment-uploader';

function makeUploadUrl(clientId: string, expiresAt: string): AttachmentUploadURL {
  return {
    client_id: clientId,
    upload_url: '/api/psc/sync/upload/mock-token/',
    expires_at: expiresAt,
  };
}

describe('FEAT-SYNC-006 attachment uploader', () => {
  beforeEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    clearPendingFiles();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    clearPendingFiles();
  });

  it('test_feat_sync_006_happy_path_upload_succeeds_on_first_attempt', async () => {
    registerFileForUpload('file-1', new Blob(['payload'], { type: 'image/jpeg' }));
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, status: 200, statusText: 'OK' })
    );

    const result = await uploadAttachments([
      makeUploadUrl('file-1', new Date(Date.now() + 60_000).toISOString()),
    ]);

    expect(result.total).toBe(1);
    expect(result.succeeded).toBe(1);
    expect(result.failed).toBe(0);
    expect(result.results[0]).toMatchObject({ success: true, attempts: 1 });
    expect(getPendingFileCount()).toBe(0);
  });

  it('test_feat_sync_006_happy_path_retries_with_exponential_backoff_then_succeeds', async () => {
    vi.useFakeTimers();

    registerFileForUpload('file-2', new Blob(['payload'], { type: 'application/pdf' }));
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Fail-1' })
      .mockResolvedValueOnce({ ok: false, status: 503, statusText: 'Fail-2' })
      .mockResolvedValueOnce({ ok: true, status: 200, statusText: 'OK' });
    vi.stubGlobal('fetch', fetchMock);

    const promise = uploadAttachments([
      makeUploadUrl('file-2', new Date(Date.now() + 60_000).toISOString()),
    ]);

    await vi.advanceTimersByTimeAsync(1_000);
    await vi.advanceTimersByTimeAsync(2_000);
    const result = await promise;

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(result.succeeded).toBe(1);
    expect(result.failed).toBe(0);
    expect(result.results[0]).toMatchObject({ success: true, attempts: 3 });
    expect(getPendingFileCount()).toBe(0);
  });

  it('test_feat_sync_006_validation_after_three_failures_item_stays_queued_for_next_sync', async () => {
    vi.useFakeTimers();

    registerFileForUpload('file-3', new Blob(['payload'], { type: 'image/jpeg' }));
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Fail-1' })
      .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Fail-2' })
      .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Fail-3' });
    vi.stubGlobal('fetch', fetchMock);

    const promise = uploadAttachments([
      makeUploadUrl('file-3', new Date(Date.now() + 60_000).toISOString()),
    ]);

    await vi.advanceTimersByTimeAsync(1_000);
    await vi.advanceTimersByTimeAsync(2_000);
    const result = await promise;

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(result.succeeded).toBe(0);
    expect(result.failed).toBe(1);
    expect(result.results[0]).toMatchObject({ success: false, attempts: 3 });
    expect(getPendingFileCount()).toBe(1);
  });

  it('test_feat_sync_006_validation_expired_upload_url_is_rejected_without_attempts', async () => {
    registerFileForUpload('file-4', new Blob(['payload'], { type: 'image/jpeg' }));
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    const result = await uploadAttachments([
      makeUploadUrl('file-4', new Date(Date.now() - 60_000).toISOString()),
    ]);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result.results[0]).toMatchObject({
      success: false,
      attempts: 0,
    });
    expect(result.results[0].error).toContain('expired');
  });

  it('test_feat_sync_006_validation_missing_pending_file_returns_failed_without_fetch', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    const result = await uploadAttachments([
      makeUploadUrl('missing-file', new Date(Date.now() + 60_000).toISOString()),
    ]);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result.results[0]).toMatchObject({
      success: false,
      attempts: 0,
    });
    expect(result.results[0].error).toContain('File not found');
  });
});

