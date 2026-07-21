import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const shipSideCircularFiles = [
  'src/legacy/vims-basic/components/circular/PdfViewer.jsx',
  'src/legacy/vims-basic/components/circular/KsmLibrary.jsx',
  'src/legacy/vims-basic/components/circular/FilterBar.jsx',
  'src/legacy/vims-basic/pages/circular/PdfViewerPage.jsx',
];

const readSource = (relativePath: string) =>
  readFileSync(resolve(process.cwd(), relativePath), 'utf8');

describe('Circular ship-side API URLs', () => {
  it('test_ship_side_circular_screens_do_not_call_localhost_api_in_production', () => {
    for (const relativePath of shipSideCircularFiles) {
      expect(readSource(relativePath), relativePath).not.toContain('localhost:8000');
    }
  });

  it('test_ship_side_circular_pdf_and_ack_calls_use_relative_backend_paths', () => {
    const pdfViewerSource = readSource('src/legacy/vims-basic/components/circular/PdfViewer.jsx');
    const standaloneViewerSource = readSource('src/legacy/vims-basic/pages/circular/PdfViewerPage.jsx');
    const librarySource = readSource('src/legacy/vims-basic/components/circular/KsmLibrary.jsx');
    const filterSource = readSource('src/legacy/vims-basic/components/circular/FilterBar.jsx');

    expect(pdfViewerSource).toContain('/api/circular/api/msc/pdf-url/');
    expect(pdfViewerSource).toContain('/api/circular/api/msc/read-ack/');
    expect(standaloneViewerSource).toContain('/api/circular/api/msc/pdf-url/');
    expect(standaloneViewerSource).toContain('/api/circular/api/msc/read-ack/');
    expect(librarySource).toContain('/api/circular/api/ship/notifications/');
    expect(librarySource).toContain('/api/circular/api/crew/notifications/');
    expect(librarySource).toContain('/api/circular/api/crew/list/');
    expect(librarySource).toContain('/api/circular/api/msc/remind-crew/');
    expect(filterSource).toContain('/api/circular/api/reports/download-pdf/');
  });
});
