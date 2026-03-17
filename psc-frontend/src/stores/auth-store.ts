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

export interface AuthState {
  // State
  tokens: AuthTokens | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;

  // Actions
  login: (credentials: LoginRequest) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<AuthTokens | null>;
  setUser: (user: AuthUser | null) => void;
  setTokens: (tokens: AuthTokens | null) => void;
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
            // Fetch user info if not already present
            const { user } = get();
            if (!user) {
              const fetchedUser = await authApi.me(currentTokens.access);
              set({ user: fetchedUser });
            }
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
