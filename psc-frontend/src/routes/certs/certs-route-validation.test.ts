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

  it('test_certs_landing_exposes_class_reconciliation_when_permitted', () => {
    expect(certsRouteSource).toContain('const canReadReconciliation = auth.hasForm?.(FORM_IDS.CERTS_RECONCILIATION) === true;');
    expect(certsRouteSource).toContain('function CertClassReconciliationEntryCard');
    expect(certsRouteSource).toContain('to={ROUTES.CERTS_RECONCILIATION}');
  });

  it('test_class_snapshot_upload_uses_vessel_dropdown_and_explains_pdf', () => {
    expect(certsRouteSource).toContain('const vesselDashboard = useFleetDashboard(canUpload);');
    expect(certsRouteSource).toContain('<Label htmlFor="classSnapshotVesselId">Vessel</Label>');
    expect(certsRouteSource).toContain('setVesselId(nextVesselId);');
    expect(certsRouteSource).toContain('normalizeSupportedClassSociety(selectedVessel?.classSociety)');
    expect(certsRouteSource).toContain('Select the vessel name. The system will use the correct vessel ID automatically.');
    expect(certsRouteSource).toContain('<Label htmlFor="classSnapshotPdf">Class Status PDF</Label>');
    expect(certsRouteSource).toContain('Do not upload an individual certificate PDF here.');
    expect(certsRouteSource).toContain('Snapshot uploaded, parsed, and reconciled.');
    expect(certsRouteSource).toContain('neither text extraction nor OCR could read usable class-status data');
    expect(certsRouteSource).not.toContain('<Label htmlFor="classSnapshotVesselId">Vessel ID</Label>');
  });

  it('test_reconciliation_review_uses_plain_language_labels', () => {
    expect(certsRouteSource).toContain('Many items need attention');
    expect(certsRouteSource).toContain('Needs setup in VIMS');
    expect(certsRouteSource).toContain('VIMS certificate record');
    expect(certsRouteSource).toContain('Class report item');
    expect(certsRouteSource).toContain('Link to VIMS certificate type');
    expect(certsRouteSource).not.toContain('Parser anomaly threshold breached');
    expect(certsRouteSource).not.toContain('Catalog / tracked item');
    expect(certsRouteSource).not.toContain('Class snapshot extract');
    expect(certsRouteSource).not.toContain('Add to ClassCodeMapping');
  });
});
