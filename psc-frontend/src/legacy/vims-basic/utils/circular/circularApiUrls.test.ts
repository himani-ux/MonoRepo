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
  it('test_circular_pdf_viewers_use_same_origin_api_base', () => {
    for (const relativePath of circularPdfHotfixFiles) {
      const source = readSource(relativePath);
      expect(source, relativePath).toContain('http://localhost:8000/api/circular/api/msc/pdf-url/');
      expect(source, relativePath).toContain('http://localhost:8000/api/circular/api/msc/read-ack/');
      expect(source, relativePath).not.toMatch(/http:\s*\/\/\s*\/api\/circular/);
    }
  });

  it('test_circular_pdf_viewers_build_query_strings_with_url_search_params', () => {
    const pdfViewerSource = readSource('src/legacy/vims-basic/components/circular/PdfViewer.jsx');
    const standaloneViewerSource = readSource('src/legacy/vims-basic/pages/circular/PdfViewerPage.jsx');

    expect(pdfViewerSource).toContain('new URLSearchParams');
    expect(standaloneViewerSource).toContain('new URLSearchParams');
  });
});
