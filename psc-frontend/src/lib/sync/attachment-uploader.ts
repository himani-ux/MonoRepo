/**
 * Attachment Uploader — uploads evidence files to presigned URLs with retry.
 *
 * Source: BACKEND_STRUCTURE.md §10.9
 * Implements: PRD.md FEAT-SYNC-006 (Attachment Upload Retry)
 *
 * Retry logic:
 * - Max 3 retries with exponential backoff (1s, 2s, 4s)
 * - After 3 failures: mark as FAILED, queue for next sync
 * - Show warning icon for failed uploads (handled by UI layer)
 */

import type { AttachmentUploadURL } from '@/lib/api/sync';

// ============================================================================
// Constants (per PRD FEAT-SYNC-006)
// ============================================================================

/** Maximum number of upload attempts per attachment */
const MAX_RETRIES = 3;

/** Exponential backoff delays in milliseconds: 1s, 2s, 4s */
const RETRY_DELAYS_MS = [1000, 2000, 4000];

// ============================================================================
// Types
// ============================================================================

/** Result of a single attachment upload attempt */
export interface AttachmentUploadResult {
  client_id: string;
  success: boolean;
  attempts: number;
  error?: string;
}

/** Overall result of uploading all attachments */
export interface UploadBatchResult {
  total: number;
  succeeded: number;
  failed: number;
  results: AttachmentUploadResult[];
}

// ============================================================================
// File Storage (in-memory cache for files pending upload)
// ============================================================================

/**
 * In-memory store for files that need to be uploaded.
 * Files are added here when evidence is queued offline,
 * and consumed when presigned URLs arrive from the push response.
 */
const pendingFiles = new Map<string, File | Blob>();

/**
 * Register a file for later upload.
 * Call this when queuing an evidence item in the sync queue.
 *
 * @param clientId The client-generated UUID for this evidence
 * @param file The actual file/blob to upload
 */
export function registerFileForUpload(
  clientId: string,
  file: File | Blob
): void {
  pendingFiles.set(clientId, file);
}

/**
 * Remove a file from the pending store after successful upload.
 */
function removePendingFile(clientId: string): void {
  pendingFiles.delete(clientId);
}

/**
 * Get a pending file by client_id.
 */
function getPendingFile(clientId: string): File | Blob | undefined {
  return pendingFiles.get(clientId);
}

// ============================================================================
// Upload Logic
// ============================================================================

/**
 * Upload all attachments to their presigned URLs.
 *
 * @param uploadUrls Array of presigned URL objects from push response
 * @returns Batch result with per-attachment status
 *
 * Implements: FEAT-SYNC-006
 */
export async function uploadAttachments(
  uploadUrls: AttachmentUploadURL[]
): Promise<UploadBatchResult> {
  const results: AttachmentUploadResult[] = [];

  for (const urlInfo of uploadUrls) {
    const result = await uploadSingleAttachment(urlInfo);
    results.push(result);
  }

  const succeeded = results.filter((r) => r.success).length;
  const failed = results.filter((r) => !r.success).length;

  return {
    total: results.length,
    succeeded,
    failed,
    results,
  };
}

/**
 * Upload a single attachment with retry logic.
 *
 * - 3 attempts with exponential backoff (1s, 2s, 4s)
 * - Returns result indicating success or failure
 * - On success: removes file from pending store
 * - On failure after all retries: file stays in pending store for next sync
 *
 * Implements: FEAT-SYNC-006
 */
async function uploadSingleAttachment(
  urlInfo: AttachmentUploadURL
): Promise<AttachmentUploadResult> {
  const file = getPendingFile(urlInfo.client_id);

  if (!file) {
    return {
      client_id: urlInfo.client_id,
      success: false,
      attempts: 0,
      error: 'File not found in pending store. Will retry on next sync.',
    };
  }

  // Check if URL has expired
  if (isUrlExpired(urlInfo.expires_at)) {
    return {
      client_id: urlInfo.client_id,
      success: false,
      attempts: 0,
      error: 'Upload URL expired. Will request new URL on next sync.',
    };
  }

  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      await performUpload(urlInfo.upload_url, file);

      // Success — remove from pending store
      removePendingFile(urlInfo.client_id);

      return {
        client_id: urlInfo.client_id,
        success: true,
        attempts: attempt + 1,
      };
    } catch (error) {
      const isLastAttempt = attempt === MAX_RETRIES - 1;
      const errorMessage =
        error instanceof Error ? error.message : 'Upload failed';

      if (isLastAttempt) {
        console.error(
          `Attachment upload failed after ${MAX_RETRIES} attempts: ` +
            `client_id=${urlInfo.client_id}, error=${errorMessage}`
        );
        return {
          client_id: urlInfo.client_id,
          success: false,
          attempts: MAX_RETRIES,
          error: errorMessage,
        };
      }

      // Wait before retry (exponential backoff)
      const delay = RETRY_DELAYS_MS[attempt] ?? RETRY_DELAYS_MS[RETRY_DELAYS_MS.length - 1];
      console.warn(
        `Attachment upload attempt ${attempt + 1} failed for ` +
          `client_id=${urlInfo.client_id}. Retrying in ${delay}ms...`
      );
      await sleep(delay);
    }
  }

  // Should not reach here, but be safe
  return {
    client_id: urlInfo.client_id,
    success: false,
    attempts: MAX_RETRIES,
    error: 'Upload failed after all retries',
  };
}

/**
 * Perform the actual HTTP upload to a presigned URL.
 *
 * Uses fetch() with PUT method since presigned URLs typically expect PUT.
 */
async function performUpload(
  uploadUrl: string,
  file: File | Blob
): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type || 'application/octet-stream',
    },
  });

  if (!response.ok) {
    throw new Error(
      `Upload failed with status ${response.status}: ${response.statusText}`
    );
  }
}

// ============================================================================
// Utilities
// ============================================================================

/** Check if a presigned URL has expired */
function isUrlExpired(expiresAt: string): boolean {
  const expiryDate = new Date(expiresAt);
  // Add 30 second buffer to account for upload time
  const now = new Date(Date.now() + 30_000);
  return now >= expiryDate;
}

/** Promise-based sleep for retry delays */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Get count of files pending upload.
 * Useful for showing pending upload count in UI.
 */
export function getPendingFileCount(): number {
  return pendingFiles.size;
}

/**
 * Clear all pending files.
 * Call on logout or when resetting sync state.
 */
export function clearPendingFiles(): void {
  pendingFiles.clear();
}
