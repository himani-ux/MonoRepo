import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const circularPdfHotfixFiles = [
  'src/legacy/vims-basic/components/circular/PdfViewer.jsx',
  'src/legacy/vims-basic/pages/circular/PdfViewerPage.jsx',
];

const circularRuntimeFiles = [
  'src/legacy/vims-basic/components/circular/FilterBar.jsx',
  'src/legacy/vims-basic/components/circular/KsmLibrary.jsx',
  'src/legacy/vims-basic/components/circular/PdfViewer.jsx',
  'src/legacy/vims-basic/pages/circular/Admin.jsx',
  'src/legacy/vims-basic/pages/circular/AdminAllNotifications.jsx',
  'src/legacy/vims-basic/pages/circular/ApprovedNotificationsLibrary.jsx',
  'src/legacy/vims-basic/pages/circular/DraftNotifications.jsx',
  'src/legacy/vims-basic/pages/circular/Officeuser.jsx',
  'src/legacy/vims-basic/pages/circular/PdfViewerPage.jsx',
  'src/legacy/vims-basic/pages/circular/UserNotifications.jsx',
];

const readSource = (relativePath: string) =>
  readFileSync(resolve(process.cwd(), relativePath), 'utf8');

describe('Circular ship-side API URLs', () => {
  it('test_circular_pdf_viewers_use_same_origin_api_base', () => {
    for (const relativePath of circularPdfHotfixFiles) {
      const source = readSource(relativePath);
      expect(source, relativePath).toContain('/api/circular/api/msc/pdf-url/');
      expect(source, relativePath).toContain('/api/circular/api/msc/read-ack/');
      expect(source, relativePath).not.toContain('http://localhost:8000');
      expect(source, relativePath).not.toMatch(/http:\s*\/\/\s*\/api\/circular/);
    }
  });

  it('test_circular_runtime_files_do_not_pin_backend_to_localhost', () => {
    for (const relativePath of circularRuntimeFiles) {
      expect(readSource(relativePath), relativePath).not.toContain('http://localhost:8000');
    }
  });

  it('test_vite_dev_server_proxies_same_origin_api_paths_to_local_django', () => {
    const viteConfigSource = readSource('vite.config.ts');

    expect(viteConfigSource).toContain("'/api'");
    expect(viteConfigSource).toContain("target: 'http://localhost:8000'");
    expect(viteConfigSource).toContain('changeOrigin: true');
  });

  it('test_circular_pdf_viewers_build_query_strings_with_url_search_params', () => {
    const pdfViewerSource = readSource('src/legacy/vims-basic/components/circular/PdfViewer.jsx');
    const standaloneViewerSource = readSource('src/legacy/vims-basic/pages/circular/PdfViewerPage.jsx');

    expect(pdfViewerSource).toContain('new URLSearchParams');
    expect(standaloneViewerSource).toContain('new URLSearchParams');
  });
});
