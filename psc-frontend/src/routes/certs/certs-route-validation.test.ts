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

  it('test_ship_side_master_messages_page_is_routed_and_plain_language', () => {
    expect(certsRouteSource).toContain('if (path === ROUTES.CERTS_MASTER_MESSAGES)');
    expect(certsRouteSource).toContain('function CertMasterMessagesPage');
    expect(certsRouteSource).toContain('Messages from office');
    expect(certsRouteSource).toContain('Class status items from office');
    expect(certsRouteSource).toContain('Mark reviewed');
  });

  it('test_vessel_certificate_table_avoids_unclear_days_and_validity_codes', () => {
    expect(certsRouteSource).not.toContain('<th className="px-3 py-3">Days</th>');
    expect(certsRouteSource).not.toContain('<span className="text-neutral-500">Days: </span>');
    expect(certsRouteSource).toContain("ST: 'Short term'");
  });

  it('test_print_and_share_forms_use_pickers_and_email_validation', () => {
    expect(certsRouteSource).toContain('function CertMultiSelectDropdown');
    expect(certsRouteSource).toContain('<Label htmlFor="printVessels">Vessels</Label>');
    expect(certsRouteSource).toContain('<Label htmlFor="bundleVessels">Vessels</Label>');
    expect(certsRouteSource).toContain('<Label htmlFor="printCustomCerts">Certificates</Label>');
    expect(certsRouteSource).toContain('<Label htmlFor="bundleCerts">Certificates</Label>');
    expect(certsRouteSource).toContain('placeholder="Choose vessels"');
    expect(certsRouteSource).toContain('placeholder="Choose certificates"');
    expect(certsRouteSource).toContain('<Input id="printRecipientEmail" type="email" inputMode="email" autoComplete="email"');
    expect(certsRouteSource).toContain('<Input id="bundleEmail" type="email" inputMode="email" autoComplete="email"');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printVessels">Vessel IDs</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="bundleVessels">Vessel IDs</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printCustomCerts">Custom certificate IDs</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="bundleCerts">Certificate IDs</Label>');
  });

  it('test_print_and_share_pickers_are_opaque_grouped_and_support_bulk_selection', () => {
    expect(certsRouteSource).toContain('className="max-h-80 w-[var(--radix-dropdown-menu-trigger-width)] border border-neutral-200 bg-white p-0 text-neutral-900 shadow-xl');
    expect(certsRouteSource).toContain('Select all');
    expect(certsRouteSource).toContain('Clear all');
    expect(certsRouteSource).toContain('function formatCertificatePickerGroup');
    expect(certsRouteSource).toContain('group: formatCertificatePickerGroup(item)');
    expect(certsRouteSource).toContain("return vessel || section || 'Other certificates';");
    expect(certsRouteSource).toContain('const groupedOptions = groupPickerOptions(resolvedOptions);');
  });
});
