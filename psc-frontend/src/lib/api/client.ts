/**
 * Axios client configuration with authentication interceptors.
 *
 * Sets up:
 * - Base URL from environment
 * - Request interceptor to add JWT token
 * - Response interceptor for automatic token refresh
 * - Error handling for auth failures
 */

import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios';
import { API_BASE_URL, API_PREFIX } from '@/lib/utils/constants';

// Create axios instance
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag to prevent multiple refresh attempts
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

/**
 * Auth store accessor type for dependency injection.
 * This avoids circular dependency issues.
 */
type AuthStoreAccessor = () => {
  tokens: { access: string; refresh: string } | null;
  refreshTokens: () => Promise<{ access: string; refresh: string } | null>;
  logout: () => void;
};

let authStoreAccessor: AuthStoreAccessor | null = null;

/**
 * Register the auth store accessor.
 * Should be called once during app initialization.
 */
export function registerAuthStoreAccessor(accessor: AuthStoreAccessor): void {
  authStoreAccessor = accessor;
}

/**
 * Get auth store state.
 */
const getAuthStore = (): ReturnType<AuthStoreAccessor> | null => {
  return authStoreAccessor?.() ?? null;
};

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = getAuthStore();
    if (authStore?.tokens?.access) {
      config.headers.Authorization = `Bearer ${authStore.tokens.access}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // If no config or already retried, reject
    if (!originalRequest) {
      return Promise.reject(error);
    }

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't retry for login/refresh endpoints
      if (
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/refresh')
      ) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue this request while refresh is in progress
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const authStore = getAuthStore();

      if (!authStore || !authStore.tokens?.refresh) {
        authStore?.logout();
        isRefreshing = false;
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const newTokens = await authStore.refreshTokens();
        if (newTokens) {
          processQueue(null, newTokens.access);
          originalRequest.headers.Authorization = `Bearer ${newTokens.access}`;
          return apiClient(originalRequest);
        } else {
          processQueue(new Error('Token refresh failed'), null);
          authStore.logout();
          window.location.href = '/login';
          return Promise.reject(error);
        }
      } catch (refreshError) {
        processQueue(refreshError as Error, null);
        authStore.logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Standard API error format from the backend.
 */
export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, string[]>;
}

/**
 * Extract error message from API error response.
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiErrorResponse | undefined;
    if (data?.message) {
      return data.message;
    }
    if (data?.details) {
      // Return first validation error
      const firstKey = Object.keys(data.details)[0];
      if (firstKey && data.details[firstKey]?.[0]) {
        return data.details[firstKey][0];
      }
    }
    if (error.message) {
      return error.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
}
