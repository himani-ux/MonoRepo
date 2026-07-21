import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const circularPdfHotfixFiles = [
  'src/legacy/vims-basic/components/circular/PdfViewer.jsx',
  'src/legacy/vims-basic/pages/circular/PdfViewerPage.jsx',
];

const readSource = (relativePath: string) =>
  readFileSync(resolve(process.cwd(), relativePath), 'utf8');

describe('Circular ship-side API URLs', () => {
  it('test_circular_pdf_viewers_do_not_call_localhost_api_in_production', () => {
    for (const relativePath of circularPdfHotfixFiles) {
      const source = readSource(relativePath);
      expect(source, relativePath).not.toContain('localhost:8000');
      expect(source, relativePath).not.toContain('http://');
      expect(source, relativePath).not.toContain('//api/circular');
      expect(source, relativePath).not.toMatch(/http:\s*\/\/\s*\/api\/circular/);
    }
  });

  it('test_circular_pdf_viewers_use_relative_backend_paths', () => {
    const pdfViewerSource = readSource('src/legacy/vims-basic/components/circular/PdfViewer.jsx');
    const standaloneViewerSource = readSource('src/legacy/vims-basic/pages/circular/PdfViewerPage.jsx');

    expect(pdfViewerSource).toContain('/api/circular/api/msc/pdf-url/');
    expect(pdfViewerSource).toContain('/api/circular/api/msc/read-ack/');
    expect(pdfViewerSource).toContain('new URLSearchParams');
    expect(standaloneViewerSource).toContain('/api/circular/api/msc/pdf-url/');
    expect(standaloneViewerSource).toContain('/api/circular/api/msc/read-ack/');
    expect(standaloneViewerSource).toContain('new URLSearchParams');
  });
});
