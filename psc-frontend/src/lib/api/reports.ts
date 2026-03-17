/**
 * DefIntel reports API functions.
 *
 * Endpoints:
 * - POST /api/psc/reports/opensource/import/
 * - POST /api/psc/reports/vessel-prep/preview/
 * - POST /api/psc/reports/vessel-prep/export/
 * - GET /api/psc/reports/defintel/predict-defcodes/
 */

import { apiClient } from './client';

interface ApiEnvelope<T> {
  data: T;
  message?: string;
}

export interface OpenSourceImportSummary {
  import_run_id: string;
  total_rows: number;
  valid_rows: number;
  inserted_rows: number;
  duplicate_rows: number;
  invalid_rows: number;
  invalid_rows_sample: Array<Record<string, unknown>>;
  duplicate_rows_sample: Array<Record<string, unknown>>;
}

export type ChecklistScopeMode =
  | 'VESSEL'
  | 'FLEET'
  | 'INSPECTOR'
  | 'FILTER_COMBINED';

export interface ChecklistFilters {
  def_code?: string[];
  action_code?: string[];
  mou?: string[];
  port?: string[];
  country?: string[];
}

export interface VesselPrepRequest {
  scope_mode: ChecklistScopeMode;
  vessel_id?: string;
  vessel_name?: string;
  inspector_name?: string;
  filters?: ChecklistFilters;
  date_from?: string;
  date_to?: string;
  dedup?: boolean;
}

export interface VesselPrepRow {
  def_code: string;
  action_code: string;
  mou: string;
  port: string;
  country: string;
  occurrence_count_total: number;
  occurrence_count_internal: number;
  occurrence_count_opensource: number;
  last_seen_date: string | null;
  example_description: string;
}

export interface VesselPrepSummary {
  row_count: number;
  occurrence_count_total: number;
  occurrence_count_internal: number;
  occurrence_count_opensource: number;
  internal_invalid_rows: number;
  input_internal_rows: number;
  input_opensource_rows: number;
  dedup_stats: {
    dedup_enabled: boolean;
    input_rows: number;
    removed_rows: number;
    output_rows: number;
  };
  last_seen_rule: string;
}

export interface VesselPrepPreviewData {
  scope_mode: ChecklistScopeMode;
  date_from: string | null;
  date_to: string | null;
  filters: ChecklistFilters;
  dedup: boolean;
  rows: VesselPrepRow[];
  summary: VesselPrepSummary;
}

export type PredictionContext = 'PORT' | 'MOU';
export type PredictionWindow = 'LAST_24_MONTHS' | 'ALL_TIME';

export interface DefIntelPredictionRequest {
  context: PredictionContext;
  port?: string;
  mou?: string;
  window?: PredictionWindow;
  top_n?: number;
}

export interface DefIntelPredictionRow {
  def_code: string;
  probability: number;
  count_context: number;
  count_global: number;
  last_seen_date: string | null;
}

export interface DefIntelPredictionData {
  context: PredictionContext;
  context_value: string;
  window: PredictionWindow;
  alpha: number;
  top_n: number;
  rows: DefIntelPredictionRow[];
  window_fallback?: string;
  window_cutoff_date?: string;
  window_cutoff_year?: number;
  invalid_rows_skipped: number;
}

export async function importOpenSourceExcel(file: File): Promise<OpenSourceImportSummary> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<ApiEnvelope<OpenSourceImportSummary>>(
    '/reports/opensource/import/',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data.data;
}

export async function previewVesselPreparationChecklist(
  payload: VesselPrepRequest
): Promise<VesselPrepPreviewData> {
  const response = await apiClient.post<ApiEnvelope<VesselPrepPreviewData>>(
    '/reports/vessel-prep/preview/',
    payload
  );
  return response.data.data;
}

export async function exportVesselPreparationChecklist(
  payload: VesselPrepRequest
): Promise<Blob> {
  const response = await apiClient.post('/reports/vessel-prep/export/', payload, {
    responseType: 'blob',
  });
  return response.data;
}

export async function predictDefCodes(
  params: DefIntelPredictionRequest
): Promise<DefIntelPredictionData> {
  const search = new URLSearchParams();
  search.set('context', params.context);
  if (params.context === 'PORT' && params.port) {
    search.set('port', params.port);
  }
  if (params.context === 'MOU' && params.mou) {
    search.set('mou', params.mou);
  }
  if (params.window) {
    search.set('window', params.window);
  }
  if (params.top_n !== undefined) {
    search.set('top_n', params.top_n.toString());
  }

  const response = await apiClient.get<ApiEnvelope<DefIntelPredictionData>>(
    `/reports/defintel/predict-defcodes/?${search.toString()}`
  );
  return response.data.data;
}

export const reportsApi = {
  importOpenSourceExcel,
  previewVesselPreparationChecklist,
  exportVesselPreparationChecklist,
  predictDefCodes,
};
