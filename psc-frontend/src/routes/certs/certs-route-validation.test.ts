import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const certsRouteSource = readFileSync(resolve(process.cwd(), 'src/routes/certs/index.tsx'), 'utf8');

describe('Certs route validation guards', () => {
  it('test_certs_route_uses_defined_error_state_component_for_failed_fetch_panels', () => {
    expect(certsRouteSource).toContain('function CertsInlineError');
    expect(certsRouteSource).not.toContain('<ErrorState');
  });

  it('test_certs_route_does_not_keep_stale_unused_symbols', () => {
    expect(certsRouteSource).not.toContain('CertOnboardingWizardState');
    expect(certsRouteSource).not.toContain('function formatJson(');
    expect(certsRouteSource).not.toContain('function formatJsonCompact(');
  });
});
