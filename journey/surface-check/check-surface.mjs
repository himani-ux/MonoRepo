// check-surface.mjs TEST_SURFACE_FILE
//
// Execution verifier for the TEST_SURFACE contract (Increment 2). For every
// `## SURFACE:` screen, loads APP_BASE_URL + route and asserts every
// allowed selector RESOLVES (>= 1 ATTACHED node — visibility at the right
// moment is the journey specs' job, this contract is about existence).
//
// Exit codes: 0 all resolved; 1 SELECTOR_STALE (each listed); 2 APP_UNREACHABLE.
// A thrown error is a non-zero exit — a crashed run is never a pass.

import { readFileSync } from 'node:fs';
import { chromium } from 'playwright';

const file = process.argv[2];
if (!file) {
  console.error('usage: node check-surface.mjs TEST_SURFACE_FILE');
  process.exit(2);
}
const base = process.env.APP_BASE_URL || 'http://localhost:4173';

// ── parse SURFACE blocks ──────────────────────────────────────────────────────
const screens = [];
let cur = null;
let inSelectors = false;
for (const line of readFileSync(file, 'utf8').split('\n')) {
  const m = line.match(/^## SURFACE: (.+?)\s*$/);
  if (m) { cur = { name: m[1], route: null, selectors: [] }; screens.push(cur); inSelectors = false; continue; }
  if (/^## /.test(line)) { cur = null; inSelectors = false; continue; }
  if (!cur) continue;
  const r = line.match(/^route:\s*(\S+)\s*$/);
  if (r) { cur.route = r[1]; continue; }
  if (/^allowed_selectors:/.test(line)) { inSelectors = true; continue; }
  if (/^[a-z_]+:/.test(line)) { inSelectors = false; continue; }
  const s = line.match(/^\s*-\s*(.+?)\s*$/);
  if (inSelectors && s) cur.selectors.push(s[1]);
}
if (screens.length === 0) {
  console.error('check-surface: no SURFACE blocks parsed — nothing to verify (fail closed)');
  process.exit(1);
}

// ── selector -> locator ───────────────────────────────────────────────────────
function locatorFor(page, sel) {
  const role = sel.match(/^role=([a-z]+)(?:\[name="(.+)"\])?$/);
  if (role) {
    return role[2] === undefined
      ? page.getByRole(role[1], { includeHidden: true })
      : page.getByRole(role[1], { name: role[2], exact: true, includeHidden: true });
  }
  const tid = sel.match(/^testid=([A-Za-z0-9_-]+)$/);
  if (tid) return page.getByTestId(tid[1]);
  return null; // grammar violations are the lint's job; treat as stale here
}

const stale = [];
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  for (const screen of screens) {
    try {
      await page.goto(base + screen.route, { waitUntil: 'domcontentloaded', timeout: 10_000 });
    } catch (e) {
      console.error(`APP_UNREACHABLE: ${base}${screen.route} (screen ${screen.name}): ${e.message}`);
      process.exitCode = 2;
      await browser.close();
      process.exit(2);
    }
    for (const sel of screen.selectors) {
      const loc = locatorFor(page, sel);
      const count = loc === null ? 0 : await loc.count();
      if (count === 0) stale.push({ screen: screen.name, sel });
    }
  }
} finally {
  await browser.close();
}

if (stale.length > 0) {
  for (const s of stale) console.error(`SELECTOR_STALE: screen ${s.screen} — [${s.sel}] does not resolve in the running app`);
  console.error(`check-surface: ${stale.length} stale selector(s) — the contract has rotted; fix the app or the surface in the SAME commit (fail closed)`);
  process.exit(1);
}
console.log(`check-surface: all selectors resolved across ${screens.length} screen(s) at ${base}`);
