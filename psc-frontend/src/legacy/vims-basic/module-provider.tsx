import { type ReactNode, useEffect } from 'react';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { useAuthStore } from '@/stores/auth-store';
import legacyStore, { persistor } from './store/store';
import { logout, setCredentials } from './services/auth/authSlice';

function LegacyAuthBridge({ children }: { children: ReactNode }) {
  const tokens = useAuthStore((state) => state.tokens);
  const user = useAuthStore((state) => state.user);

  useEffect(() => {
    if (!tokens?.access || !user) {
      legacyStore.dispatch(logout());
      return;
    }
    const legacyUserType = user.legacy_user_type ?? (user.user_type === 'vessel' ? 'ship' : 'office');
    const username = user.username ?? user.UserName ?? user.login_id ?? user.crew_id ?? user.employee_id ?? user.id;

    legacyStore.dispatch(
      setCredentials({
        accessToken: tokens.access,
        refreshToken: tokens.refresh,
        user: {
          ...user,
          user_type: legacyUserType,
          display_name: user.display_name ?? user.full_name,
          role_name: user.role_name ?? user.role,
          role: user.role_name ?? user.role,
          work_side: user.work_side ?? (legacyUserType === 'ship' ? 1 : 0),
          form_ids: user.form_ids ?? [],
          process_ids: user.process_ids ?? [],
          first_name: user.first_name ?? '',
          surname: user.surname ?? '',
          is_chief: user.is_chief ?? false,
          username,
          UserName: user.UserName ?? username,
        },
      })
    );
  }, [tokens, user]);

  return <>{children}</>;
}

export function LegacyBasicProvider({ children }: { children: ReactNode }) {
  return (
    <Provider store={legacyStore}>
      <PersistGate loading={null} persistor={persistor}>
        <LegacyAuthBridge>{children}</LegacyAuthBridge>
      </PersistGate>
    </Provider>
  );
}
