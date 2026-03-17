import { useEffect, useState } from 'react';
import axios from 'axios';
import { Download, FileSpreadsheet, Search, Upload, WifiOff } from 'lucide-react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import { useToast } from '@/hooks/use-toast';
import { useOffline } from '@/hooks/use-offline';
import { useAuth } from '@/hooks/use-auth';
import { useDashboard } from '@/hooks/use-dashboard';
import { getErrorMessage } from '@/lib/api/client';
import {
  reportsApi,
  type ChecklistScopeMode,
  type DefIntelPredictionData,
  type PredictionContext,
  type PredictionWindow,
  type OpenSourceImportSummary,
  type VesselPrepPreviewData,
  type VesselPrepRequest,
} from '@/lib/api/reports';

type OpenSourceState = 'unknown' | 'available' | 'missing';

const scopeModes: ChecklistScopeMode[] = ['VESSEL', 'FLEET', 'INSPECTOR', 'FILTER_COMBINED'];
const predictionContexts: PredictionContext[] = ['PORT', 'MOU'];
const predictionWindows: PredictionWindow[] = ['LAST_24_MONTHS', 'ALL_TIME'];

interface ApiErrorPayload {
  error?: string;
}

function parseCsv(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function isReachabilityError(error: unknown): boolean {
  if (!axios.isAxiosError(error)) {
    return false;
  }
  return !error.response;
}

function getApiErrorCode(error: unknown): string | undefined {
  if (!axios.isAxiosError(error)) {
    return undefined;
  }
  const data = error.response?.data as ApiErrorPayload | undefined;
  return data?.error;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const { toast } = useToast();
  const { isOnline } = useOffline();
  const { isOffice, vesselId: authVesselId, canImportOpenSource } = useAuth();
  const {
    data: dashboardData,
    isError: hasVesselError,
    error: vesselError,
  } = useDashboard(undefined, { enabled: isOffice });

  const [apiReachable, setApiReachable] = useState(true);

  const [openSourceFile, setOpenSourceFile] = useState<File | null>(null);
  const [openSourceImportSummary, setOpenSourceImportSummary] = useState<OpenSourceImportSummary | null>(
    null
  );
  const [openSourceState, setOpenSourceState] = useState<OpenSourceState>('unknown');
  const [importing, setImporting] = useState(false);

  const [scopeMode, setScopeMode] = useState<ChecklistScopeMode>('VESSEL');
  const [selectedVesselId, setSelectedVesselId] = useState('');
  const [inspectorName, setInspectorName] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [dedup, setDedup] = useState(true);
  const [filterDefCode, setFilterDefCode] = useState('');
  const [filterActionCode, setFilterActionCode] = useState('');
  const [filterMou, setFilterMou] = useState('');
  const [filterPort, setFilterPort] = useState('');
  const [filterCountry, setFilterCountry] = useState('');
  const [checklistPreview, setChecklistPreview] = useState<VesselPrepPreviewData | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [exportingChecklist, setExportingChecklist] = useState(false);

  const [predictionContext, setPredictionContext] = useState<PredictionContext>('PORT');
  const [predictionPort, setPredictionPort] = useState('');
  const [predictionMou, setPredictionMou] = useState('');
  const [predictionWindow, setPredictionWindow] = useState<PredictionWindow>('LAST_24_MONTHS');
  const [topN, setTopN] = useState(20);
  const [predictionResult, setPredictionResult] = useState<DefIntelPredictionData | null>(null);
  const [predicting, setPredicting] = useState(false);

  const vesselOptions = dashboardData?.vessels ?? [];
  const effectiveVesselId = isOffice ? selectedVesselId : (authVesselId ?? '');

  const onlineRequired = !isOnline || !apiReachable;
  const showImportRequired = scopeMode === 'FILTER_COMBINED' && openSourceState === 'missing';
  const vesselSelectionMissing = scopeMode === 'VESSEL' && !effectiveVesselId;
  const predictionContextValue = predictionContext === 'PORT' ? predictionPort : predictionMou;

  useEffect(() => {
    if (!isOffice) {
      return;
    }
    if (hasVesselError && isReachabilityError(vesselError)) {
      setApiReachable(false);
    }
  }, [hasVesselError, isOffice, vesselError]);

  useEffect(() => {
    if (!isOffice || selectedVesselId || vesselOptions.length === 0) {
      return;
    }
    setSelectedVesselId(vesselOptions[0].id);
  }, [isOffice, selectedVesselId, vesselOptions]);

  const buildChecklistPayload = (): VesselPrepRequest | null => {
    const payload: VesselPrepRequest = {
      scope_mode: scopeMode,
      dedup,
    };

    if (dateFrom) {
      payload.date_from = dateFrom;
    }
    if (dateTo) {
      payload.date_to = dateTo;
    }

    if (scopeMode === 'VESSEL') {
      if (!effectiveVesselId) {
        return null;
      }
      payload.vessel_id = effectiveVesselId;
      if (isOffice) {
        const selectedVessel = vesselOptions.find((vessel) => vessel.id === effectiveVesselId);
        if (selectedVessel?.vessel_name) {
          payload.vessel_name = selectedVessel.vessel_name;
        }
      }
    }

    if (scopeMode === 'INSPECTOR') {
      const normalizedInspector = inspectorName.trim();
      if (!normalizedInspector) {
        return null;
      }
      payload.inspector_name = normalizedInspector;
    }

    if (scopeMode === 'FILTER_COMBINED') {
      payload.filters = {
        def_code: parseCsv(filterDefCode),
        action_code: parseCsv(filterActionCode),
        mou: parseCsv(filterMou),
        port: parseCsv(filterPort),
        country: parseCsv(filterCountry),
      };
    }

    return payload;
  };

  const handleError = (error: unknown, title: string) => {
    if (isReachabilityError(error)) {
      setApiReachable(false);
      return;
    }
    toast({
      variant: 'destructive',
      title,
      description: getErrorMessage(error),
    });
  };

  const handleImportOpenSource = async () => {
    if (!openSourceFile) {
      toast({
        variant: 'destructive',
        title: 'Select a file',
        description: 'Choose a monthly OpenSource Excel file before importing.',
      });
      return;
    }
    if (onlineRequired) {
      return;
    }

    setImporting(true);
    try {
      const summary = await reportsApi.importOpenSourceExcel(openSourceFile);
      setApiReachable(true);
      setOpenSourceState('available');
      setOpenSourceImportSummary(summary);
      toast({
        title: 'Import completed',
        description: `Inserted ${summary.inserted_rows} rows, duplicates ${summary.duplicate_rows}.`,
      });
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 403) {
        toast({
          variant: 'destructive',
          title: 'Office only',
          description: getErrorMessage(error),
        });
      } else {
        handleError(error, 'Import failed');
      }
    } finally {
      setImporting(false);
    }
  };

  const handleChecklistPreview = async () => {
    if (onlineRequired) {
      return;
    }
    const checklistPayload = buildChecklistPayload();
    if (!checklistPayload) {
      toast({
        variant: 'destructive',
        title: 'Invalid checklist input',
        description: 'Provide required scope inputs before preview.',
      });
      return;
    }

    setPreviewing(true);
    try {
      const preview = await reportsApi.previewVesselPreparationChecklist(checklistPayload);
      setApiReachable(true);
      if (scopeMode === 'FILTER_COMBINED') {
        setOpenSourceState('available');
      }
      setChecklistPreview(preview);
    } catch (error) {
      if (scopeMode === 'FILTER_COMBINED' && getApiErrorCode(error) === 'IMPORT_REQUIRED') {
        setOpenSourceState('missing');
        setChecklistPreview(null);
      } else {
        handleError(error, 'Preview failed');
      }
    } finally {
      setPreviewing(false);
    }
  };

  const handleChecklistExport = async () => {
    if (onlineRequired) {
      return;
    }
    const checklistPayload = buildChecklistPayload();
    if (!checklistPayload) {
      toast({
        variant: 'destructive',
        title: 'Invalid checklist input',
        description: 'Provide required scope inputs before export.',
      });
      return;
    }

    setExportingChecklist(true);
    try {
      const blob = await reportsApi.exportVesselPreparationChecklist(checklistPayload);
      setApiReachable(true);
      if (scopeMode === 'FILTER_COMBINED') {
        setOpenSourceState('available');
      }
      downloadBlob(
        blob,
        `Vessel_Preparation_Checklist_${new Date().toISOString().slice(0, 10)}.xlsx`
      );
    } catch (error) {
      if (scopeMode === 'FILTER_COMBINED' && getApiErrorCode(error) === 'IMPORT_REQUIRED') {
        setOpenSourceState('missing');
      } else {
        handleError(error, 'Export failed');
      }
    } finally {
      setExportingChecklist(false);
    }
  };

  const handlePrediction = async () => {
    const trimmedContextValue = predictionContextValue.trim();
    if (!trimmedContextValue) {
      toast({
        variant: 'destructive',
        title: 'Missing prediction input',
        description: predictionContext === 'PORT' ? 'Enter a port value.' : 'Enter an MOU value.',
      });
      return;
    }
    if (onlineRequired) {
      return;
    }

    setPredicting(true);
    try {
      const result = await reportsApi.predictDefCodes({
        context: predictionContext,
        port: predictionContext === 'PORT' ? trimmedContextValue : undefined,
        mou: predictionContext === 'MOU' ? trimmedContextValue : undefined,
        window: predictionWindow,
        top_n: topN,
      });
      setApiReachable(true);
      setPredictionResult(result);
    } catch (error) {
      handleError(error, 'Prediction failed');
    } finally {
      setPredicting(false);
    }
  };

  return (
    <RootLayout>
      <PageHeader
        title="DefIntel Reports"
        subtitle="OpenSource import, checklist builder, and probability prediction"
      />

      <div className="space-y-6 pb-24">
        {onlineRequired && (
          <Card className="border-error-200 bg-error-50">
            <CardContent className="flex items-center justify-between gap-4 p-4">
              <div className="flex items-center gap-3">
                <WifiOff className="h-5 w-5 text-error-600" />
                <div>
                  <p className="font-medium text-error-700">Online required</p>
                  <p className="text-sm text-error-600">
                    This DefIntel screen requires an active API connection.
                  </p>
                </div>
              </div>
              {isOnline && !apiReachable && (
                <Button variant="outline" onClick={() => setApiReachable(true)}>
                  Retry
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {canImportOpenSource && (
          <Card>
            <CardHeader>
              <CardTitle>A) Import OpenSource Excel (monthly)</CardTitle>
              <CardDescription>Upload monthly OpenSource deficiency data to enable combined analysis.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-center">
                <Input
                  type="file"
                  accept=".xlsx"
                  onChange={(event) => setOpenSourceFile(event.target.files?.[0] ?? null)}
                  aria-label="OpenSource Excel file"
                />
                <Button
                  onClick={handleImportOpenSource}
                  disabled={importing || onlineRequired || !openSourceFile}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  {importing ? 'Importing...' : 'Import OpenSource'}
                </Button>
              </div>

              {openSourceImportSummary && (
                <div className="grid gap-3 text-sm md:grid-cols-5">
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-neutral-500">Total rows</p>
                    <p className="text-lg font-semibold text-neutral-800">
                      {openSourceImportSummary.total_rows}
                    </p>
                  </div>
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-neutral-500">Valid rows</p>
                    <p className="text-lg font-semibold text-neutral-800">
                      {openSourceImportSummary.valid_rows}
                    </p>
                  </div>
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-neutral-500">Inserted rows</p>
                    <p className="text-lg font-semibold text-neutral-800">
                      {openSourceImportSummary.inserted_rows}
                    </p>
                  </div>
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-neutral-500">Duplicate rows</p>
                    <p className="text-lg font-semibold text-neutral-800">
                      {openSourceImportSummary.duplicate_rows}
                    </p>
                  </div>
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-neutral-500">Invalid rows</p>
                    <p className="text-lg font-semibold text-neutral-800">
                      {openSourceImportSummary.invalid_rows}
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>B) Checklist Builder (scope modes + preview + export)</CardTitle>
            <CardDescription>
              Build vessel preparation checklist rows from internal data and optional OpenSource combined scope.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">Scope mode</label>
                <Select value={scopeMode} onValueChange={(value) => setScopeMode(value as ChecklistScopeMode)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {scopeModes.map((mode) => (
                      <SelectItem key={mode} value={mode}>
                        {mode}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {scopeMode === 'VESSEL' && isOffice && (
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700">Vessel</label>
                  <Select value={selectedVesselId} onValueChange={setSelectedVesselId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select vessel" />
                    </SelectTrigger>
                    <SelectContent>
                      {vesselOptions.map((vessel) => (
                        <SelectItem key={vessel.id} value={vessel.id}>
                          {vessel.vessel_code} - {vessel.vessel_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {scopeMode === 'VESSEL' && !isOffice && (
                <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3 text-sm text-neutral-600">
                  Vessel scope uses your assigned vessel automatically.
                </div>
              )}

              {vesselSelectionMissing && (
                <div className="rounded-md border border-error-200 bg-error-50 p-3 text-sm text-error-700">
                  Select vessel
                </div>
              )}

              {scopeMode === 'INSPECTOR' && (
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700">Inspector name</label>
                  <Input
                    value={inspectorName}
                    onChange={(event) => setInspectorName(event.target.value)}
                    placeholder="e.g. John Doe"
                  />
                </div>
              )}

              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">Date from</label>
                <Input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">Date to</label>
                <Input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
              </div>
            </div>

            {scopeMode === 'FILTER_COMBINED' && (
              <div className="grid gap-3 md:grid-cols-2">
                <Input
                  value={filterDefCode}
                  onChange={(event) => setFilterDefCode(event.target.value)}
                  placeholder="Def code(s), comma-separated"
                />
                <Input
                  value={filterActionCode}
                  onChange={(event) => setFilterActionCode(event.target.value)}
                  placeholder="Action code(s), comma-separated"
                />
                <Input
                  value={filterMou}
                  onChange={(event) => setFilterMou(event.target.value)}
                  placeholder="MOU value(s), comma-separated"
                />
                <Input
                  value={filterPort}
                  onChange={(event) => setFilterPort(event.target.value)}
                  placeholder="Port value(s), comma-separated"
                />
                <Input
                  value={filterCountry}
                  onChange={(event) => setFilterCountry(event.target.value)}
                  placeholder="Country value(s), comma-separated"
                />
              </div>
            )}

            <label className="flex items-center gap-2 text-sm text-neutral-700">
              <input
                type="checkbox"
                checked={dedup}
                onChange={(event) => setDedup(event.target.checked)}
              />
              Apply dedup after merge
            </label>

            {showImportRequired && (
              <div className="rounded-md border border-warning-300 bg-warning-50 p-3 text-warning-800">
                Import required
              </div>
            )}

            <div className="flex flex-wrap items-center gap-2">
              <Button
                onClick={handleChecklistPreview}
                disabled={previewing || onlineRequired || vesselSelectionMissing}
              >
                <Search className="mr-2 h-4 w-4" />
                {previewing ? 'Loading Preview...' : 'Preview'}
              </Button>
              <Button
                variant="outline"
                onClick={handleChecklistExport}
                disabled={exportingChecklist || onlineRequired || vesselSelectionMissing}
              >
                <Download className="mr-2 h-4 w-4" />
                {exportingChecklist ? 'Exporting...' : 'Export Checklist'}
              </Button>
            </div>

            {checklistPreview && (
              <div className="space-y-3">
                <div className="grid gap-3 text-sm md:grid-cols-4">
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-neutral-500">Rows</p>
                    <p className="font-semibold text-neutral-800">{checklistPreview.summary.row_count}</p>
                  </div>
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-neutral-500">Occurrences (total)</p>
                    <p className="font-semibold text-neutral-800">
                      {checklistPreview.summary.occurrence_count_total}
                    </p>
                  </div>
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-neutral-500">Occurrences (internal)</p>
                    <p className="font-semibold text-neutral-800">
                      {checklistPreview.summary.occurrence_count_internal}
                    </p>
                  </div>
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-neutral-500">Occurrences (opensource)</p>
                    <p className="font-semibold text-neutral-800">
                      {checklistPreview.summary.occurrence_count_opensource}
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-md border border-neutral-200">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-neutral-100 text-neutral-700">
                      <tr>
                        <th className="px-3 py-2">DEF Code</th>
                        <th className="px-3 py-2">Action</th>
                        <th className="px-3 py-2">MOU</th>
                        <th className="px-3 py-2">Port</th>
                        <th className="px-3 py-2">Country</th>
                        <th className="px-3 py-2">Total</th>
                        <th className="px-3 py-2">Internal</th>
                        <th className="px-3 py-2">OpenSource</th>
                        <th className="px-3 py-2">Last Seen</th>
                      </tr>
                    </thead>
                    <tbody>
                      {checklistPreview.rows.map((row) => (
                        <tr key={`${row.def_code}-${row.action_code}-${row.mou}-${row.port}-${row.country}`}>
                          <td className="px-3 py-2">{row.def_code}</td>
                          <td className="px-3 py-2">{row.action_code}</td>
                          <td className="px-3 py-2">{row.mou}</td>
                          <td className="px-3 py-2">{row.port}</td>
                          <td className="px-3 py-2">{row.country || '-'}</td>
                          <td className="px-3 py-2">{row.occurrence_count_total}</td>
                          <td className="px-3 py-2">{row.occurrence_count_internal}</td>
                          <td className="px-3 py-2">{row.occurrence_count_opensource}</td>
                          <td className="px-3 py-2">{row.last_seen_date || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>C) Prediction (PORT/MOU + window + top_n)</CardTitle>
            <CardDescription>Predict top deficiency codes using combined historical frequency.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">Context</label>
                <Select
                  value={predictionContext}
                  onValueChange={(value) => setPredictionContext(value as PredictionContext)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {predictionContexts.map((context) => (
                      <SelectItem key={context} value={context}>
                        {context}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">
                  {predictionContext === 'PORT' ? 'Port' : 'MOU'}
                </label>
                <Input
                  value={predictionContext === 'PORT' ? predictionPort : predictionMou}
                  onChange={(event) =>
                    predictionContext === 'PORT'
                      ? setPredictionPort(event.target.value)
                      : setPredictionMou(event.target.value)
                  }
                  placeholder={predictionContext === 'PORT' ? 'e.g. Singapore' : 'e.g. Tokyo'}
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">Window</label>
                <Select
                  value={predictionWindow}
                  onValueChange={(value) => setPredictionWindow(value as PredictionWindow)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {predictionWindows.map((windowOption) => (
                      <SelectItem key={windowOption} value={windowOption}>
                        {windowOption}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">Top N</label>
                <Input
                  type="number"
                  min={1}
                  max={100}
                  value={topN}
                  onChange={(event) => setTopN(Number(event.target.value) || 1)}
                />
              </div>
            </div>

            <Button onClick={handlePrediction} disabled={predicting || onlineRequired}>
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              {predicting ? 'Predicting...' : 'Run Prediction'}
            </Button>

            {predictionResult && (
              <div className="overflow-x-auto rounded-md border border-neutral-200">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-neutral-100 text-neutral-700">
                    <tr>
                      <th className="px-3 py-2">DEF Code</th>
                      <th className="px-3 py-2">Probability</th>
                      <th className="px-3 py-2">Context Count</th>
                      <th className="px-3 py-2">Global Count</th>
                      <th className="px-3 py-2">Last Seen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictionResult.rows.map((row) => (
                      <tr key={row.def_code}>
                        <td className="px-3 py-2">{row.def_code}</td>
                        <td className="px-3 py-2">{row.probability.toFixed(6)}</td>
                        <td className="px-3 py-2">{row.count_context}</td>
                        <td className="px-3 py-2">{row.count_global}</td>
                        <td className="px-3 py-2">{row.last_seen_date || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </RootLayout>
  );
}
