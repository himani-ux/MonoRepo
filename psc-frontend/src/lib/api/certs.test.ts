import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiClientMock = vi.hoisted(() => ({
  post: vi.fn(),
}));

vi.mock('@/lib/api/client', () => ({
  apiClient: apiClientMock,
}));

vi.mock('@/lib/utils/constants', () => ({
  API_BASE_URL: 'http://localhost:8000',
}));

import { certsApi } from './certs';

describe('certsApi certificate uploads', () => {
  beforeEach(() => {
    apiClientMock.post.mockReset();
  });

  it('uses an extended timeout for certificate PDF upload processing', async () => {
    apiClientMock.post.mockResolvedValue({ data: { ok: true } });
    const file = new File(['%PDF-1.4'], 'certificate.pdf', { type: 'application/pdf' });

    await certsApi.uploadTrackedItemPdf('tracked-1', {
      file,
      context: 'office',
      reason: 'Uploaded for review.',
    });

    expect(apiClientMock.post).toHaveBeenCalledWith(
      'http://localhost:8000/api/certs/tracked-items/tracked-1/upload-pdf/',
      expect.any(FormData),
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      }
    );

    const formData = apiClientMock.post.mock.calls[0]?.[1] as FormData;
    expect(formData.get('file')).toBe(file);
    expect(formData.get('context')).toBe('office');
    expect(formData.get('reason')).toBe('Uploaded for review.');
  });

  it('uses the OCR request timeout when re-reading an existing certificate PDF', async () => {
    apiClientMock.post.mockResolvedValue({ data: { ok: true } });

    await certsApi.reparseTrackedItemPdf('tracked-1', {
      context: 'vessel',
      reason: 'Read the PDF again.',
    });

    expect(apiClientMock.post).toHaveBeenCalledWith(
      'http://localhost:8000/api/certs/tracked-items/tracked-1/reparse-pdf/',
      {
        context: 'vessel',
        reason: 'Read the PDF again.',
      },
      { timeout: 120000 }
    );
  });
});
