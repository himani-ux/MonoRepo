/**
 * Settings API functions — company logo upload.
 */

import { apiClient } from './client';

export interface CompanyLogoStatus {
  has_logo: boolean;
  logo_url: string | null;
}

/**
 * Get company logo status.
 * GET /api/psc/auth/company-logo/
 */
export async function getCompanyLogo(): Promise<CompanyLogoStatus> {
  const response = await apiClient.get<{ data: CompanyLogoStatus }>(
    '/auth/company-logo/'
  );
  return response.data.data;
}

/**
 * Upload company logo (office users only).
 * POST /api/psc/auth/company-logo/
 */
export async function uploadCompanyLogo(
  file: File
): Promise<CompanyLogoStatus> {
  const formData = new FormData();
  formData.append('logo', file);

  const response = await apiClient.post<{
    data: CompanyLogoStatus;
    message: string;
  }>('/auth/company-logo/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data.data;
}
