import axios from 'axios';
import { API_BASE_URL } from '@/lib/utils/constants';

interface PaginatedResponse<T> {
  results?: T[];
}

export interface OrbVessel {
  id: string;
  vesselName: string | null;
  vesselCode: string | null;
  imonumber?: string | null;
}

export interface OrbApprovedEntry {
  id: string;
  date: string;
  code: string;
  item_no: string | null;
  record_of_operation: string | null;
  status: string;
  created_by?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  entry_no?: number | null;
  is_deleted?: boolean;
  master_print?: string | null;
}

const orbClient = axios.create({
  baseURL: `${API_BASE_URL}/api/orb/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

function normalizeListResponse<T>(payload: T[] | PaginatedResponse<T>): T[] {
  if (Array.isArray(payload)) {
    return payload;
  }

  return payload.results ?? [];
}

async function fetchVessels(): Promise<OrbVessel[]> {
  const response = await orbClient.get<OrbVessel[] | PaginatedResponse<OrbVessel>>('/vessels/');
  return normalizeListResponse(response.data);
}

async function fetchApprovedEntries(vesselId: string): Promise<OrbApprovedEntry[]> {
  const response = await orbClient.get<OrbApprovedEntry[]>('/approved-entries/', {
    params: { vessel_id: vesselId },
  });
  return Array.isArray(response.data) ? response.data : [];
}

export const orbApi = {
  fetchVessels,
  fetchApprovedEntries,
};
