/**
 * Authentication store using Zustand with persistence.
 *
 * Manages:
 * - JWT tokens (access and refresh)
 * - User information
 * - Authentication state
 * - Token refresh logic
 *
 * Per FRONTEND_GUIDELINES.md Section 4.2
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { authApi, type AuthUser, type LoginRequest } from '@/lib/api/auth';
import { registerAuthStoreAccessor } from '@/lib/api/client';
import type { AuthTokens } from '@/types';
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  TOKEN_EXPIRY_BUFFER_MS,
} from '@/lib/utils/constants';

export const OFFICE_IDLE_TIMEOUT_MS = 8 * 60 * 60 * 1000;
export const VESSEL_IDLE_TIMEOUT_MS = 24 * 60 * 60 * 1000;
export const SESSION_WARNING_THRESHOLDS_MS = [15 * 60 * 1000, 5 * 60 * 1000] as const;

const LEGACY_AUTH_STORAGE_KEYS = [
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  'accessToken',
  'refreshToken',
  'user',
] as const;

export function clearLegacyAuthStorage(): void {
  for (const key of LEGACY_AUTH_STORAGE_KEYS) {
    localStorage.removeItem(key);
  }
}

/**
 * Decode JWT token to get expiration time.
 * Returns null if token is invalid.
 */
function decodeTokenExp(token: string): number | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = JSON.parse(atob(parts[1]));
    return payload.exp ? payload.exp * 1000 : null; // Convert to milliseconds
  } catch {
    return null;
  }
}

/**
 * Check if token is expired or will expire within the buffer time.
 */
function isTokenExpired(token: string, bufferMs: number = 0): boolean {
  const exp = decodeTokenExp(token);
  if (!exp) return true;
  return Date.now() + bufferMs >= exp;
}

export interface ReauthIdentifier {
  label: 'Crew ID' | 'Employee ID';
  value: string;
}

export function getSessionTimeoutMs(user: AuthUser | null): number {
  return user?.user_type === 'vessel' ? VESSEL_IDLE_TIMEOUT_MS : OFFICE_IDLE_TIMEOUT_MS;
}

export function getReauthIdentifier(user: AuthUser | null): ReauthIdentifier {
  if (user?.user_type === 'vessel') {
    return {
      label: 'Crew ID',
      value: user.crew_id || user.login_id || user.username || '',
    };
  }

  return {
    label: 'Employee ID',
    value: user?.employee_id || user?.login_id || user?.username || '',
  };
}

export interface AuthState {
  // State
  tokens: AuthTokens | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  isReauthRequired: boolean;
  sessionLastActivityAt: number;

  // Actions
  login: (credentials: LoginRequest) => Promise<AuthUser>;
  reauthenticate: (password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<AuthTokens | null>;
  setUser: (user: AuthUser | null) => void;
  setTokens: (tokens: AuthTokens | null) => void;
  markSessionActivity: (timestamp?: number) => void;
  requireReauth: () => void;
  initialize: () => Promise<void>;
  checkAndRefreshToken: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      tokens: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      isInitialized: false,
      isReauthRequired: false,
      sessionLastActivityAt: Date.now(),

      /**
       * Login with credentials.
       * Stores tokens and user information.
       */
      login: async (credentials: LoginRequest) => {
        set({ isLoading: true });
        try {
          const response = await authApi.login(credentials);

          const tokens: AuthTokens = {
            access: response.access,
            refresh: response.refresh,
          };

          set({
            tokens,
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            isReauthRequired: false,
            sessionLastActivityAt: Date.now(),
          });

          clearLegacyAuthStorage();

          return response.user;
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      reauthenticate: async (password: string) => {
        const { user } = get();
        const identifier = getReauthIdentifier(user);

        if (!identifier.value) {
          throw new Error('Unable to resolve session identifier.');
        }

        set({ isLoading: true });
        try {
          const response = await authApi.login({
            username: identifier.value,
            password,
          });

          const tokens: AuthTokens = {
            access: response.access,
            refresh: response.refresh,
          };

          set({
            tokens,
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            isReauthRequired: false,
            sessionLastActivityAt: Date.now(),
          });

          clearLegacyAuthStorage();

          return response.user;
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      /**
       * Logout user.
       * Clears tokens and user state.
       */
      logout: async () => {
        const { tokens } = get();

        // Call logout API (fire and forget)
        if (tokens?.access) {
          authApi.logout(tokens.access, tokens.refresh).catch(() => {
            // Ignore errors
          });
        }

        // Clear state
        set({
          tokens: null,
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isReauthRequired: false,
        });

        clearLegacyAuthStorage();
      },

      /**
       * Refresh access token using refresh token.
       * Returns new tokens or null if refresh fails.
       */
      refreshTokens: async () => {
        const { tokens } = get();

        if (!tokens?.refresh) {
          return null;
        }

        // Check if refresh token is also expired
        if (isTokenExpired(tokens.refresh)) {
          set({
            tokens: null,
            user: null,
            isAuthenticated: false,
            isReauthRequired: false,
          });
          clearLegacyAuthStorage();
          return null;
        }

        try {
          const newTokens = await authApi.refresh(tokens.refresh);

          set({
            tokens: newTokens,
            isAuthenticated: true,
          });

          return newTokens;
        } catch {
          // Refresh failed - clear auth state
          set({
            tokens: null,
            user: null,
            isAuthenticated: false,
            isReauthRequired: false,
          });
          clearLegacyAuthStorage();
          return null;
        }
      },

      /**
       * Check if access token needs refresh and refresh if needed.
       * Returns true if we have valid auth, false otherwise.
       */
      checkAndRefreshToken: async () => {
        const { tokens, refreshTokens } = get();

        if (!tokens?.access) {
          set({
            tokens: null,
            user: null,
            isAuthenticated: false,
            isReauthRequired: false,
          });
          return false;
        }

        // Check if access token is about to expire
        if (isTokenExpired(tokens.access, TOKEN_EXPIRY_BUFFER_MS)) {
          const newTokens = await refreshTokens();
          return newTokens !== null;
        }

        return true;
      },

      /**
       * Set user directly (used after token decode).
       */
      setUser: (user) => {
        set({ user, isAuthenticated: user !== null });
      },

      /**
       * Set tokens directly.
       */
      setTokens: (tokens) => {
        set({
          tokens,
          isAuthenticated: tokens !== null,
        });
      },

      markSessionActivity: (timestamp = Date.now()) => {
        if (get().isReauthRequired) {
          return;
        }
        set({ sessionLastActivityAt: timestamp });
      },

      requireReauth: () => {
        set({ isReauthRequired: true });
      },

      /**
       * Initialize auth state from stored tokens.
       * Validates tokens and fetches user info if needed.
       */
      initialize: async () => {
        const { tokens, checkAndRefreshToken } = get();

        if (!tokens?.access) {
          set({
            tokens: null,
            user: null,
            isAuthenticated: false,
            isLoading: false,
            isInitialized: true,
            isReauthRequired: false,
          });
          return;
        }

        set({ isLoading: true });

        try {
          // Check and refresh token if needed
          const hasValidAuth = await checkAndRefreshToken();

          if (!hasValidAuth) {
            set({
              isLoading: false,
              isInitialized: true,
            });
            return;
          }

          // Get current tokens after potential refresh
          const currentTokens = get().tokens;

          if (currentTokens?.access) {
            // Always refresh the user snapshot so server-side permission seed changes
            // are reflected even when a stale user object was persisted locally.
            const fetchedUser = await authApi.me(currentTokens.access);
            set({ user: fetchedUser });
          }

          set({
            isLoading: false,
            isInitialized: true,
          });
        } catch {
          // Clear invalid auth state
          set({
            tokens: null,
            user: null,
            isAuthenticated: false,
            isLoading: false,
            isInitialized: true,
            isReauthRequired: false,
          });
          clearLegacyAuthStorage();
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Only persist tokens and user
        tokens: state.tokens,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        sessionLastActivityAt: state.sessionLastActivityAt,
      }),
    }
  )
);

// Register auth store accessor with API client
// This breaks the circular dependency between auth-store and client
registerAuthStoreAccessor(() => ({
  tokens: useAuthStore.getState().tokens,
  refreshTokens: useAuthStore.getState().refreshTokens,
  logout: useAuthStore.getState().logout,
}));

// Legacy token keys for backward compatibility
// (in case tokens were stored separately before)
export function migrateLegacyTokens(): void {
  const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

  if (accessToken && refreshToken) {
    const { tokens, setTokens } = useAuthStore.getState();

    // Only migrate if store doesn't have tokens
    if (!tokens) {
      setTokens({
        access: accessToken,
        refresh: refreshToken,
      });
    }

    clearLegacyAuthStorage();
    return;
  }

  clearLegacyAuthStorage();
}
