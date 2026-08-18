// fixture-app/server.mjs — zero-dependency invoice fixture app (Increment 2).
// Implements the golden AFJ-001 (upload malformed -> schema_error inline ->
// corrected -> ACCEPTED) and AFJ-002 (Retry on a REJECTED row -> ACCEPTED)
// flows behind the golden TEST_SURFACE contract. In-memory state per run.
//
// Public API (the ONLY endpoints — matches TEST_SURFACE public_api):
//   GET  /invoices            -> HTML (browser) or JSON rows (Accept: application/json)
//   POST /invoices/import     -> { name, content } -> row { name, status, error }

import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, 'index.html'));
const port = Number(process.env.PORT || 4173);

const rows = []; // { name, status: 'ACCEPTED' | 'REJECTED', error }

function validate(content) {
  const firstLine = String(content).split('\n')[0].trim();
  if (firstLine === 'file,amount') return { status: 'ACCEPTED', error: null };
  return { status: 'REJECTED', error: 'schema_error: first line must be "file,amount"' };
}

const server = createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${port}`);
  if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/invoices')) {
    if ((req.headers.accept || '').includes('application/json')) {
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify(rows));
      return;
    }
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(html);
    return;
  }
  if (req.method === 'POST' && url.pathname === '/invoices/import') {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      let parsed;
      try { parsed = JSON.parse(body); } catch {
        res.writeHead(400, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ error: 'invalid JSON' }));
        return;
      }
      const { name, content, replaces } = parsed;
      const { status, error } = validate(content);
      if (replaces) {
        const i = rows.findIndex((r) => r.name === replaces);
        if (i >= 0) rows.splice(i, 1);
      }
      const existing = rows.findIndex((r) => r.name === name);
      const row = { name, status, error };
      if (existing >= 0) rows[existing] = row; else rows.push(row);
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify(row));
    });
    return;
  }
  res.writeHead(404, { 'content-type': 'text/plain' });
  res.end('not found');
});

server.listen(port, () => console.log(`fixture-app listening on http://localhost:${port}`));
