import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { buildCircularAttachmentUrl } from './attachmentUrl';

const readSource = (relativePath: string) =>
  readFileSync(resolve(process.cwd(), relativePath), 'utf8');

describe('buildCircularAttachmentUrl', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('test_circular_pending_request_pdf_link_uses_backend_media_origin_in_local_vite', () => {
    vi.stubGlobal('window', {
      location: {
        origin: 'http://localhost:5173',
        hostname: 'localhost',
      },
    });

    expect(buildCircularAttachmentUrl('/media/circular/attachments/test.pdf')).toBe(
      'http://localhost:8000/media/circular/attachments/test.pdf',
    );
  });

  it('test_circular_pending_request_pdf_link_normalizes_legacy_api_media_path', () => {
    vi.stubGlobal('window', {
      location: {
        origin: 'http://localhost:5173',
        hostname: 'localhost',
      },
    });

    expect(buildCircularAttachmentUrl('/api/circular/media/circular/attachments/test.pdf')).toBe(
      'http://localhost:8000/media/circular/attachments/test.pdf',
    );
  });

  it('test_circular_pending_request_pdf_link_keeps_same_origin_media_on_non_local_server', () => {
    vi.stubGlobal('window', {
      location: {
        origin: 'https://vims.example.com',
        hostname: 'vims.example.com',
      },
    });

    expect(buildCircularAttachmentUrl('/media/circular/attachments/test.pdf')).toBe(
      '/media/circular/attachments/test.pdf',
    );
  });

  it('test_circular_pending_request_pdf_link_keeps_absolute_url', () => {
    expect(buildCircularAttachmentUrl('https://files.example.com/test.pdf')).toBe(
      'https://files.example.com/test.pdf',
    );
  });

  it('test_circular_office_route_uses_backend_aware_pdf_links_in_active_component', () => {
    const routesSource = readSource('src/legacy/vims-basic/routes/circular/CircularRoutes.jsx');
    const officeSource = readSource('src/legacy/vims-basic/pages/circular/Officeuser.jsx');
    const approvedLibrarySource = readSource(
      'src/legacy/vims-basic/pages/circular/ApprovedNotificationsLibrary.jsx',
    );

    expect(routesSource).toContain('import Admin from "../../pages/circular/Officeuser"');
    expect(officeSource).toContain('buildCircularAttachmentUrl');
    expect(officeSource).toContain('href={buildCircularAttachmentUrl(viewingRequest.attachment_url)}');
    expect(officeSource).not.toMatch(/href=\{\/\^https\?:\\\/\\\//);
    expect(approvedLibrarySource).toContain('href={buildCircularAttachmentUrl(n.attachment_url)}');
    expect(approvedLibrarySource).not.toMatch(/href=\{\/\^https\?:\\\/\\\//);
  });

  it('test_circular_office_upload_pages_enforce_50mb_pdf_attachment_limit', () => {
    const officeSource = readSource('src/legacy/vims-basic/pages/circular/Officeuser.jsx');
    const adminSource = readSource('src/legacy/vims-basic/pages/circular/Admin.jsx');

    for (const source of [officeSource, adminSource]) {
      expect(source).toContain('const MAX_CIRCULAR_ATTACHMENT_SIZE_MB = 50');
      expect(source).toContain('MAX_CIRCULAR_ATTACHMENT_SIZE_BYTES');
      expect(source).toContain('Each PDF attachment must not exceed');
      expect(source).toContain('Number(file?.size || 0) > MAX_CIRCULAR_ATTACHMENT_SIZE_BYTES');
    }
  });

  it('test_circular_office_authoring_pages_use_same_origin_api_paths', () => {
    const officeSource = readSource('src/legacy/vims-basic/pages/circular/Officeuser.jsx');
    const adminSource = readSource('src/legacy/vims-basic/pages/circular/Admin.jsx');

    expect(officeSource).not.toContain('http://localhost:8000');
    expect(adminSource).not.toContain('http://localhost:8000');
    expect(officeSource).toContain('fetch("/api/circular/api/document-types/"');
    expect(adminSource).toContain("fetch('/api/circular/api/document-types/'");
  });
});
