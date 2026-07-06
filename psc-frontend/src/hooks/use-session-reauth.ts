import { useCallback, useEffect, useMemo, useRef } from 'react';
import { toast } from '@/hooks/use-toast';
import {
  getReauthIdentifier,
  getSessionTimeoutMs,
  SESSION_WARNING_THRESHOLDS_MS,
  useAuthStore,
} from '@/stores/auth-store';

const ACTIVITY_EVENTS = ['click', 'keydown', 'pointerdown', 'touchstart'] as const;

export function useSessionReauth() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isReauthRequired = useAuthStore((state) => state.isReauthRequired);
  const isSubmitting = useAuthStore((state) => state.isLoading);
  const sessionLastActivityAt = useAuthStore((state) => state.sessionLastActivityAt);
  const markSessionActivity = useAuthStore((state) => state.markSessionActivity);
  const requireReauth = useAuthStore((state) => state.requireReauth);
  const reauthenticate = useAuthStore((state) => state.reauthenticate);
  const logout = useAuthStore((state) => state.logout);
  const warnedThresholds = useRef<Set<number>>(new Set());

  const timeoutMs = getSessionTimeoutMs(user);
  const identifier = useMemo(() => getReauthIdentifier(user), [user]);

  const evaluateSession = useCallback(() => {
    if (!isAuthenticated || isReauthRequired) {
      return;
    }

    const elapsedMs = Date.now() - sessionLastActivityAt;
    const remainingMs = timeoutMs - elapsedMs;

    if (remainingMs <= 0) {
      requireReauth();
      return;
    }

    for (const thresholdMs of SESSION_WARNING_THRESHOLDS_MS) {
      if (remainingMs <= thresholdMs && !warnedThresholds.current.has(thresholdMs)) {
        warnedThresholds.current.add(thresholdMs);
        toast.warning({
          title: `Session expires in ${Math.round(thresholdMs / 60000)} minutes`,
          description: 'Save your work or continue activity to keep the session active.',
        });
      }
    }

    if (remainingMs > SESSION_WARNING_THRESHOLDS_MS[0]) {
      warnedThresholds.current.clear();
    }
  }, [isAuthenticated, isReauthRequired, requireReauth, sessionLastActivityAt, timeoutMs]);

  useEffect(() => {
    if (!isAuthenticated) {
      warnedThresholds.current.clear();
      return undefined;
    }

    const onActivity = () => {
      if (!useAuthStore.getState().isReauthRequired) {
        warnedThresholds.current.clear();
        markSessionActivity();
      }
    };

    for (const eventName of ACTIVITY_EVENTS) {
      window.addEventListener(eventName, onActivity, { passive: true });
    }

    const intervalId = window.setInterval(evaluateSession, 1000);
    evaluateSession();

    return () => {
      window.clearInterval(intervalId);
      for (const eventName of ACTIVITY_EVENTS) {
        window.removeEventListener(eventName, onActivity);
      }
    };
  }, [evaluateSession, isAuthenticated, markSessionActivity]);

  return {
    identifier,
    isReauthRequired,
    isSubmitting,
    logout,
    reauthenticate,
  };
}

