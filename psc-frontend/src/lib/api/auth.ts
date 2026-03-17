/**
 * Authentication API functions.
 *
 * Endpoints per BACKEND_STRUCTURE.md and apps/accounts/views.py:
 * - POST /api/psc/auth/login/
 * - POST /api/psc/auth/refresh/
 * - POST /api/psc/auth/logout/
 * - GET /api/psc/auth/me/
 */

import axios from 'axios';
import { API_BASE_URL, API_PREFIX } from '@/lib/utils/constants';
import type { AuthTokens } from '@/types';

// Create a separate axios instance for auth that doesn't use interceptors
// This prevents circular dependencies and infinite loops during token refresh
const authClient = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * User data returned from login/me endpoints.
 */
export interface AuthUser {
  id: string;
  /** Normalized to lowercase: 'vessel' | 'office' */
  user_type: 'vessel' | 'office';
  login_id?: string | null;
  full_name: string;
  role: string;
  vessel_id: string | null;
  vessel_name?: string | null;
  vessel_code: string | null;
  email: string | null;
  employee_id: string | null;
  crew_id: string | null;
  rank: string | null;
  department?: string | null;
  form_ids: string[];
  process_ids: string[];
  has_global_vessel_access?: boolean | null;
  display_name?: string;
  role_name?: string;
  username?: string;
  UserName?: string;
  work_side?: number;
  first_name?: string;
  surname?: string;
  is_chief?: boolean;
  legacy_user_type?: 'ship' | 'office';
}

/**
 * Login request payload.
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * Login response from the API.
 */
export interface LoginResponse {
  data: {
    access: string;
    refresh: string;
    user: AuthUser;
  };
  message: string;
}

/**
 * Token refresh response from the API.
 */
export interface RefreshResponse {
  data: {
    access: string;
    refresh: string;
  };
  message: string;
}

/**
 * Current user response from the API.
 */
export interface MeResponse {
  data: AuthUser;
  message: string;
}

/**
 * Normalize user_type from backend (VESSEL/OFFICE) to lowercase (vessel/office).
 */
function normalizeIdList(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        return parsed.map((item) => String(item).trim()).filter(Boolean);
      }
    } catch {
      // fallthrough
    }
    return value.split(',').map((item) => item.trim()).filter(Boolean);
  }
  return [];
}

function normalizeUser(user: AuthUser): AuthUser {
  return {
    ...user,
    user_type: user.user_type?.toLowerCase() as AuthUser['user_type'],
    form_ids: normalizeIdList((user as AuthUser).form_ids),
    process_ids: normalizeIdList((user as AuthUser).process_ids),
  };
}

/**
 * Authentication API functions.
 */
export const authApi = {
  /**
   * Login with username and password.
   * Returns tokens and user information.
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse['data']> => {
    const { data } = await authClient.post<LoginResponse>(
      '/auth/login/',
      credentials
    );
    return { ...data.data, user: normalizeUser(data.data.user) };
  },

  /**
   * Refresh the access token using a refresh token.
   * Returns new access and refresh tokens.
   */
  refresh: async (refreshToken: string): Promise<AuthTokens> => {
    const { data } = await authClient.post<RefreshResponse>('/auth/refresh/', {
      refresh: refreshToken,
    });
    return {
      access: data.data.access,
      refresh: data.data.refresh,
    };
  },

  /**
   * Logout the user.
   * Optionally sends the refresh token to be blacklisted (if backend supports it).
   */
  logout: async (
    accessToken: string,
    refreshToken?: string
  ): Promise<void> => {
    try {
      await authClient.post(
        '/auth/logout/',
        { refresh: refreshToken },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
    } catch {
      // Ignore logout errors - token might already be invalid
      // Frontend will clear tokens regardless
    }
  },

  /**
   * Get current user information from the token.
   */
  me: async (accessToken: string): Promise<AuthUser> => {
    const { data } = await authClient.get<MeResponse>('/auth/me/', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
    return normalizeUser(data.data);
  },
};
