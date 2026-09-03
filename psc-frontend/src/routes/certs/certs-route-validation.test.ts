import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const certsRouteSource = readFileSync(resolve(process.cwd(), 'src/routes/certs/index.tsx'), 'utf8');
const certsApiSource = readFileSync(resolve(process.cwd(), 'src/lib/api/certs.ts'), 'utf8');

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
    expect(certsRouteSource).toContain('<Label htmlFor="classSnapshotReportDate">Report date from PDF</Label>');
    expect(certsRouteSource).toContain('setReportDateFromPdf(event.target.value)');
    expect(certsRouteSource).toContain('printedOnDate: reportDateFromPdf || null');
    expect(certsApiSource).toContain("formData.append('printedOnDate', payload.printedOnDate);");
    expect(certsRouteSource).toContain('<Label htmlFor="classSnapshotPdf">Class Status PDF</Label>');
    expect(certsRouteSource).toContain('The report date must come from the PDF, never from the upload date.');
    expect(certsRouteSource).toContain('the report date could not be read');
    expect(certsRouteSource).toContain('Snapshot uploaded, parsed, and reconciled.');
    expect(certsRouteSource).toContain('neither text extraction nor OCR could read usable class-status data');
    expect(certsRouteSource).not.toContain('<Label htmlFor="classSnapshotVesselId">Vessel ID</Label>');
    expect(certsRouteSource).not.toContain('printedOnDate: uploadFile');
  });

  it('test_reconciliation_review_uses_plain_language_labels', () => {
    expect(certsRouteSource).toContain('<th className="px-3 py-3">Printed On</th>');
    expect(certsRouteSource).toContain('<td className="px-3 py-3 text-neutral-700">{formatDate(run.printedOnDate)}</td>');
    expect(certsRouteSource.indexOf('<th className="px-3 py-3">Findings</th>')).toBeLessThan(
      certsRouteSource.indexOf('<th className="px-3 py-3">Printed On</th>')
    );
    const printedOnHeaderIndex = certsRouteSource.indexOf('<th className="px-3 py-3">Printed On</th>');
    expect(printedOnHeaderIndex).toBeGreaterThan(0);
    expect(printedOnHeaderIndex).toBeLessThan(
      certsRouteSource.indexOf('<th className="px-3 py-3">Action</th>', printedOnHeaderIndex)
    );
    expect(certsRouteSource).toContain('Many items need attention');
    expect(certsRouteSource).toContain("{ bucket: 'match', label: 'Match'");
    expect(certsRouteSource).toContain("{ bucket: 'mismatch', label: 'Different'");
    expect(certsRouteSource).toContain("{ bucket: 'missing_in_catalog', label: 'Add to VIMS'");
    expect(certsRouteSource).toContain("{ bucket: 'conditional_stc', label: 'Short term'");
    expect(certsRouteSource).toContain('Conditions of class');
    expect(certsRouteSource).toContain("const RECONCILIATION_HIDE_WHEN_EMPTY_BUCKETS = new Set(['extended_postponed', 'unmapped_low_confidence']);");
    expect(certsRouteSource).toContain('VIMS certificate record');
    expect(certsRouteSource).toContain('Class report item');
    expect(certsRouteSource).toContain('Link to VIMS certificate type');
    expect(certsRouteSource).toContain('getVisibleReconciliationBucketTabs(run.data)');
    expect(certsRouteSource).toContain('<ClassSnapshotPdfButton snapshotId={run.snapshotId}>');
    expect(certsRouteSource).toContain("const showDiffRows = flag.bucket !== 'conditions_of_class';");
    expect(certsRouteSource).toContain('{showDiffRows && diffRows.length > 0 ? (');
    expect(certsRouteSource).toContain("const selectedIsConditionOfClass = selectedFlag?.bucket === 'conditions_of_class';");
    expect(certsRouteSource).toContain('!selectedIsConditionOfClass ? <CertReconciliationCatalogPanel run={run.data} flag={selectedFlag} /> : null');
    expect(certsRouteSource).toContain("{ label: 'Due date', value: extract.due_date ?? extract.dueDate }");
    expect(certsRouteSource).toContain("{ label: 'Summary', value: extract.raw_text ?? extract.rawText }");
    expect(certsRouteSource.indexOf("{ label: 'Summary', value: extract.raw_text ?? extract.rawText }")).toBeLessThan(
      certsRouteSource.indexOf("{ label: 'Due date', value: extract.due_date ?? extract.dueDate }")
    );
    expect(certsRouteSource).toContain('formatReconciliationDefinitionValue(label, value)');
    expect(certsRouteSource).toContain('whitespace-pre-wrap break-words');
    expect(certsRouteSource).toContain("if (label !== 'Summary')");
    expect(certsRouteSource).toContain('function formatClassReportSummaryText');
    expect(certsRouteSource).not.toContain('Parser anomaly threshold breached');
    expect(certsRouteSource).not.toContain('Condition or class note found in the class report.');
    expect(certsRouteSource).not.toContain("label: 'Already matched'");
    expect(certsRouteSource).not.toContain("label: 'Details differ'");
    expect(certsRouteSource).not.toContain("label: 'Different from VIMS'");
    expect(certsRouteSource).not.toContain("label: 'Needs setup in VIMS'");
    expect(certsRouteSource).not.toContain("label: 'Not found in class report'");
    expect(certsRouteSource).not.toContain("label: 'Missing in class report'");
    expect(certsRouteSource).not.toContain("label: 'Short-term certificate'");
    expect(certsRouteSource).not.toContain("label: 'Extended or postponed'");
    expect(certsRouteSource).not.toContain("label: 'Needs manual check'");
    expect(certsRouteSource).not.toContain('href={certsApi.getClassSnapshotPdfViewUrl');
    expect(certsRouteSource).not.toContain("label: 'Text found in class report'");
    expect(certsRouteSource).not.toContain("label: 'Section in class report'");
    expect(certsRouteSource).not.toContain("label: 'Condition ID'");
    expect(certsRouteSource).not.toContain("label: 'Postponed until'");
    expect(certsRouteSource).not.toContain('Catalog / tracked item');
    expect(certsRouteSource).not.toContain('Class snapshot extract');
    expect(certsRouteSource).not.toContain('Add to ClassCodeMapping');
  });

  it('test_reconciliation_dashboard_empty_state_does_not_reference_vessel_filters', () => {
    const start = certsRouteSource.indexOf('function CertReconciliationDashboardPage()');
    const end = certsRouteSource.indexOf('function CertParserOpsPage()', start);
    const reconciliationDashboardSource = certsRouteSource.slice(start, end);

    expect(start).toBeGreaterThanOrEqual(0);
    expect(end).toBeGreaterThan(start);
    expect(reconciliationDashboardSource).toContain('No class snapshots have been reconciled yet.');
    expect(reconciliationDashboardSource).not.toContain('filtersActive');
  });

  it('test_reconciliation_review_formats_diff_values_without_json_and_opens_snapshot_pdf', () => {
    expect(certsRouteSource).toContain("formatReconciliationDiffValue(value, 'vims')");
    expect(certsRouteSource).toContain("formatReconciliationDiffValue(value, 'class')");
    expect(certsRouteSource).toContain('function formatReadableReviewValue');
    expect(certsRouteSource).not.toContain("formatUnknown(diff?.class ?? diff?.snapshot ?? value)");
    expect(certsApiSource).toContain('getClassSnapshotPdfViewUrl(id: string): string');
    expect(certsApiSource).toContain('getClassSnapshotPdfBlob(id: string): Promise<Blob>');
    expect(certsApiSource).toContain("`/class-snapshots/${encodeURIComponent(id)}/pdf/view/`");
    expect(certsApiSource).toContain("responseType: 'blob'");
    expect(certsRouteSource).toContain('function ClassSnapshotPdfButton');
    expect(certsRouteSource).toContain('certsApi.getClassSnapshotPdfBlob(snapshotId)');
    expect(certsRouteSource).toContain("window.open('', '_blank')");
    expect(certsRouteSource).toContain('URL.createObjectURL(blob)');
  });

  it('test_ship_side_master_messages_page_is_routed_and_plain_language', () => {
    expect(certsRouteSource).toContain('if (path === ROUTES.CERTS_MASTER_MESSAGES)');
    expect(certsRouteSource).toContain('function CertMasterMessagesPage');
    expect(certsRouteSource).toContain('Messages from office');
    expect(certsRouteSource).toContain('Class status items from office');
    expect(certsRouteSource).toContain('Open class status PDF');
    expect(certsRouteSource).toContain('<ClassSnapshotPdfButton snapshotId={message.snapshotId} size="sm" showIcon={false}>');
    expect(certsRouteSource).toContain('Mark reviewed');
  });

  it('test_vessel_dashboard_opens_latest_class_status_pdf_without_office_message', () => {
    expect(certsRouteSource).toContain('className="flex flex-wrap gap-2 lg:flex-nowrap"');
    expect(certsRouteSource).toContain('variant="outline" className="whitespace-nowrap"');
    expect(certsRouteSource).toContain('font-medium text-neutral-900 lg:whitespace-nowrap');
    expect(certsRouteSource).toContain('className="min-w-0 space-y-3"');
    expect(certsRouteSource).toContain('className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-3"');
    expect(certsRouteSource).toContain('className="break-words font-medium text-neutral-900">{vessel.currentMaster');
    expect(certsRouteSource).not.toContain('className="font-medium text-neutral-900 lg:whitespace-nowrap">{vessel.currentMaster');
    expect(certsRouteSource).toContain('data.lastClassSnapshot?.id ? (');
    expect(certsRouteSource).toContain('<ClassSnapshotPdfButton snapshotId={data.lastClassSnapshot.id} className="whitespace-nowrap">');
    expect(certsRouteSource).toContain('Open class status PDF');
    expect(certsRouteSource).toContain("return 'Report date not set';");
    expect(certsRouteSource).not.toContain('snapshot.printedOnDate ?? snapshot.uploadedAt');
  });

  it('test_vessel_certificate_table_avoids_unclear_days_and_validity_codes', () => {
    expect(certsRouteSource).not.toContain('<th className="px-3 py-3">Days</th>');
    expect(certsRouteSource).not.toContain('<span className="text-neutral-500">Days: </span>');
    expect(certsRouteSource).toContain("ST: 'Short term'");
  });

  it('test_vessel_certificate_table_uses_icon_actions_for_upload_and_pdf_view', () => {
    expect(certsRouteSource).toContain('function CertVesselItemActions');
    expect(certsRouteSource).toContain('const hasPdf = Boolean(item.pdfAttachmentId);');
    expect(certsRouteSource).toContain('<UploadCloud className="h-4 w-4" aria-hidden="true" />');
    expect(certsRouteSource).toContain('<Eye className="h-4 w-4" aria-hidden="true" />');
    expect(certsRouteSource).toContain('disabled={!hasPdf || viewLoading}');
    expect(certsRouteSource).toContain('const blobId = item.pdfAttachmentId;');
    expect(certsRouteSource).toContain('certsApi.getTrackedItemPdfBlob(item.id, blobId)');
    expect(certsRouteSource).not.toContain('<Link to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(imo, item.id)}>{actionLabel(item)}</Link>');
  });

  it('test_certificate_detail_allows_active_pdf_to_be_read_again', () => {
    expect(certsRouteSource).toContain('useReparseTrackedItemPdf');
    expect(certsRouteSource).toContain('const reparseMutation = useReparseTrackedItemPdf(item.id, imo);');
    expect(certsRouteSource).toContain('const handleReparsePdf = () => {');
    expect(certsRouteSource).toContain("reparseMutation.mutate({ reason: 'Certificate PDF read again from detail screen.' });");
    expect(certsRouteSource).toContain("{reparseMutation.isPending ? 'Reading...' : 'Read PDF again'}");
    expect(certsRouteSource).toContain('getErrorMessage(reparseMutation.error)');
  });

  it('test_catalog_editor_uses_dropdowns_vessel_names_and_no_hard_purge_action', () => {
    expect(certsRouteSource).toContain('const CATALOG_VALIDITY_TYPE_OPTIONS');
    expect(certsRouteSource).toContain('const CATALOG_ISSUING_AUTHORITY_TYPE_OPTIONS');
    expect(certsRouteSource).toContain('const CATALOG_SUBMISSION_SCOPE_OPTIONS');
    expect(certsRouteSource).toContain('function CertCatalogTextOrSelectField');
    expect(certsRouteSource).toContain('function CertCatalogVesselDropdown');
    expect(certsRouteSource).toContain('getCatalogPrintSectionLabelOptions(loadedCatalogRows, sections.data ?? [])');
    expect(certsRouteSource).toContain('cleanCatalogIntegerInput(event.target.value)');
    expect(certsRouteSource).toContain('<Label htmlFor="createSpecificVessels">Specific vessels</Label>');
    expect(certsRouteSource).toContain('<Label htmlFor="detailSpecificVessels">Specific vessels</Label>');
    expect(certsRouteSource).toContain('Choose vessel names. The system will use the correct vessel IDs automatically.');
    expect(certsRouteSource).not.toContain('Specific vessel IDs');
    expect(certsRouteSource).not.toContain('createSpecificVesselIds');
    expect(certsRouteSource).not.toContain('detailSpecificVesselIds');
    expect(certsRouteSource).not.toContain('useHardPurgeCatalogRow');
    expect(certsRouteSource).not.toContain('Confirm hard purge');
  });

  it('test_catalog_writer_gate_checks_profile_role_before_generic_office_role', () => {
    expect(certsRouteSource).toContain('function getCatalogWriterRoleCandidates');
    expect(certsRouteSource).toContain('return [auth.user?.role_name, auth.user?.safety_role_name, auth.role]');
    expect(certsRouteSource).toContain('function hasCatalogWriterRole');
    expect(certsRouteSource).toContain('return hasEditPermission && hasCatalogWriterRole(auth);');
    expect(certsRouteSource).toContain('return hasBulkPermission && hasCatalogWriterRole(auth);');
  });

  it('test_print_and_share_forms_use_context_vessel_section_pickers_and_email_validation', () => {
    expect(certsRouteSource).toContain('function CertMultiSelectDropdown');
    expect(certsRouteSource).toContain('const contextVesselId = resolveContextVesselId(initialVesselId, auth.vesselId);');
    expect(certsRouteSource).toContain('const sections = useCatalogSections();');
    expect(certsRouteSource).toContain('Open a vessel first to print that vessel.');
    expect(certsRouteSource).toContain('Open a vessel first to create a share bundle.');
    expect(certsRouteSource).toContain('<PageHeader title="Print certs status" />');
    expect(certsRouteSource).toContain('<CardTitle>Print certs status</CardTitle>');
    expect(certsRouteSource).toContain('<Label htmlFor="printCertificateList">Certificate sections</Label>');
    expect(certsRouteSource).toContain('<SelectItem value={PRINT_ALL_SECTIONS_OPTION}>All sections</SelectItem>');
    expect(certsRouteSource).toContain("const selectedSection = certificateListSelection === PRINT_ALL_SECTIONS_OPTION ? '' : certificateListSelection;");
    expect(certsRouteSource).toContain("scope: selectedSection ? 'per_vessel_partial' : 'per_vessel_full'");
    expect(certsRouteSource).toContain('sections: selectedSection ? [selectedSection] : []');
    expect(certsRouteSource).toContain('customCertIds: []');
    expect(certsRouteSource).toContain("watermarkApplied: 'NONE'");
    expect(certsRouteSource).toContain('<Label htmlFor="bundleSections">Certificate sections</Label>');
    expect(certsRouteSource).toContain('placeholder="Choose sections"');
    expect(certsRouteSource).toContain('sections: selectedSections,');
    expect(certsRouteSource).toContain('disabled={mutation.isPending || vesselIds.length === 0 || selectedSections.length === 0}');
    expect(certsRouteSource).toContain('<Input id="bundleEmail" type="email" inputMode="email" autoComplete="email"');
    expect(certsRouteSource).toContain('Print certs status');
    expect(certsRouteSource).not.toContain('Print this vessel');
    expect(certsRouteSource).not.toContain('Print builder');
    expect(certsRouteSource).not.toContain('function buildCertCertificatePickerOptions');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printScope">Scope</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printStatus">Status</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printSections">Sections</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printWatermark">Watermark</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printWatermarkRecipient">Watermark recipient</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printRecipientEmail">Recipient email</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printCustomCerts">Certificates</Label>');
    expect(certsRouteSource).not.toContain('id="printCustomCerts"');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printVessels">');
    expect(certsRouteSource).not.toContain('<Label htmlFor="bundleVessels">');
    expect(certsRouteSource).not.toContain('placeholder="Choose vessels"');
    expect(certsRouteSource).not.toContain('<Label htmlFor="printCustomCerts">Custom certificate IDs</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="bundleCerts">Certificate IDs</Label>');
    expect(certsRouteSource).not.toContain('<Label htmlFor="bundleCerts">Certificates</Label>');
    expect(certsRouteSource).not.toContain('placeholder="Choose certificates"');
  });

  it('test_print_and_share_certificate_pickers_are_scoped_to_context_vessel_queries', () => {
    expect(certsRouteSource).toContain('function useCertPrintSelectionOptions(filters: CertTrackedItemFilters, enabled: boolean)');
    expect(certsRouteSource).toContain('const trackedItems = useTrackedItems({ ...filters, page: 1, pageSize: 1 }, enabled);');
    expect(certsRouteSource).toContain('const printSelectionFilters: CertTrackedItemFilters = contextVesselId');
    expect(certsRouteSource).toContain('? { vesselId: contextVesselId }');
    expect(certsRouteSource).toContain('const printSelectionEnabled = canPrint && Boolean(contextVesselId);');
    expect(certsRouteSource).toContain('const printSelection = useCertPrintSelectionOptions(printSelectionFilters, printSelectionEnabled);');
    expect(certsRouteSource).toContain('contextVesselId ? { vesselId: contextVesselId } : {}');
    expect(certsRouteSource).toContain('canShareBundle && Boolean(contextVesselId)');
    expect(certsRouteSource).not.toContain('useTrackedItems({}, enabled);');
    expect(certsRouteSource).not.toContain('requiresVesselContext');
  });

  it('test_print_and_share_pickers_are_opaque_grouped_and_support_bulk_selection', () => {
    expect(certsRouteSource).toContain('className="max-h-80 w-[var(--radix-dropdown-menu-trigger-width)] border border-neutral-200 bg-white p-0 text-neutral-900 shadow-xl');
    expect(certsRouteSource).toContain('Select all');
    expect(certsRouteSource).toContain('Clear all');
    expect(certsRouteSource).toContain('function buildCertSectionPickerOptions');
    expect(certsRouteSource).toContain('function buildCertSectionPickerOptions(sections: CertCatalogSection[])');
    expect(certsRouteSource).toContain('const sectionOptions = buildCertSectionPickerOptions(sections.data ?? []);');
    expect(certsRouteSource).toContain('value: String(section.sectionId || section.sectionCode)');
    expect(certsRouteSource).toContain('label: section.displayName');
    expect(certsRouteSource).toContain('const groupedOptions = groupPickerOptions(resolvedOptions);');
    expect(certsRouteSource).not.toContain('function formatCertificatePickerGroup');
    expect(certsRouteSource).not.toContain('function formatCertificatePickerCategory');
  });

  it('test_print_and_share_results_offer_real_downloads_and_email_status', () => {
    expect(certsRouteSource).toContain('function CertPrintArtifactSummary');
    expect(certsRouteSource).toContain('<dt className="text-neutral-500">Generated</dt>');
    expect(certsRouteSource).toContain('<dt className="text-neutral-500">Pages</dt>');
    expect(certsRouteSource).not.toContain('<dt className="text-neutral-500">Scope</dt>');
    expect(certsRouteSource).not.toContain('<dt className="text-neutral-500">Hash</dt>');
    expect(certsRouteSource).not.toContain('<dt className="text-neutral-500">Watermark</dt>');
    expect(certsRouteSource).not.toContain('<dt className="text-neutral-500">Recipient</dt>');
    expect(certsRouteSource).toContain('function CertPrintArtifactDownloads');
    expect(certsRouteSource).toContain('Download PDF');
    expect(certsRouteSource).toContain('Download Excel');
    expect(certsRouteSource).toContain('Download ZIP');
    expect(certsRouteSource).toContain('certsApi.downloadPrintArtifact(artifact.printId, kind)');
    expect(certsRouteSource).toContain('function CertPrintEmailStatus');
    expect(certsRouteSource).toContain('Email sent to');
    expect(certsRouteSource).not.toContain("ZIP {artifact.bundleZipBlobId ? 'ready' : 'n/a'}");
  });
});
