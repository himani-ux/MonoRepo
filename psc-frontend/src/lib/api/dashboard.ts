/**
 * Dashboard API functions
 *
 * Fetches aggregated dashboard metrics from the backend.
 */

import { apiClient } from './client';

// ============================================================================
// Response Types
// ============================================================================

export interface InspectionsByType {
  inspection_type: string;
  count: number;
}

export interface TopDefCode {
  def_code: string;
  def_code_description: string;
  count: number;
}

export interface CARStatusCount {
  status: string;
  count: number;
}

export interface MonthlyDefTrend {
  month: string; // "YYYY-MM"
  count: number;
}

export interface RepeatDeficiencyVessel {
  vessel_id: string;
  vesselName: string;
  vesselcode?: string;
}

export interface RepeatDeficiencyGroup {
  def_code: string;
  def_title: string;
  repeat_count: number;
  classification?: string;
  vessels: RepeatDeficiencyVessel[];
  range_from?: string;
  range_to?: string;
}

export interface VesselOption {
  id: string;
  vessel_name: string;
  vessel_code: string;
}

export interface DashboardData {
  inspections_by_type: InspectionsByType[];
  total_inspections_12m: number;
  open_cars_count: number;
  overdue_cars_count: number;
  detentions_count: number;
  top_def_codes: TopDefCode[];
  pending_defs_count: number;
  missing_evidence_count: number;
  overdue_actions_count: number;
  car_status_distribution: CARStatusCount[];
  monthly_def_trend: MonthlyDefTrend[];
  cars_due_soon_count?: number;
  repeat_deficiencies?: RepeatDeficiencyGroup[];
  vessels: VesselOption[];
}

export interface DashboardResponse {
  data: DashboardData;
}

// ============================================================================
// API Functions
// ============================================================================

export async function fetchDashboard(vesselId?: string): Promise<DashboardData> {
  const params: Record<string, string> = {};
  if (vesselId) params.vessel_id = vesselId;

  const response = await apiClient.get<DashboardResponse>('/dashboard/', { params });
  return response.data.data;
}
