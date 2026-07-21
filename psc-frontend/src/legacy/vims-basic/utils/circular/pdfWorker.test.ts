import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const readSource = (relativePath: string) =>
  readFileSync(resolve(process.cwd(), relativePath), 'utf8');

const helperSource = readSource('src/legacy/vims-basic/utils/circular/pdfWorker.js');
const dashboardViewerSource = readSource('src/legacy/vims-basic/components/circular/PdfViewer.jsx');
const standaloneViewerSource = readSource('src/legacy/vims-basic/pages/circular/PdfViewerPage.jsx');

describe('Circular PDF worker configuration', () => {
  it('test_circular_pdf_viewers_use_vite_bundled_worker_instance', () => {
    expect(helperSource).toContain('pdf.worker.min.mjs?worker');
    expect(helperSource).toContain('new PdfWorker({ type: "module" })');
    expect(helperSource).toContain('GlobalWorkerOptions.workerPort = workerPort');

    expect(dashboardViewerSource).toContain('configurePdfJsWorker(pdfjsLib)');
    expect(standaloneViewerSource).toContain('configurePdfJsWorker(pdfjsLib)');
  });

  it('test_circular_pdf_viewers_do_not_load_worker_from_mjs_asset_url', () => {
    expect(dashboardViewerSource).not.toContain('new URL("pdfjs-dist/build/pdf.worker.min.mjs"');
    expect(dashboardViewerSource).not.toContain('"pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url');
    expect(standaloneViewerSource).not.toContain('new URL("pdfjs-dist/build/pdf.worker.min.mjs"');
    expect(standaloneViewerSource).not.toContain('"pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url');
  });
});
