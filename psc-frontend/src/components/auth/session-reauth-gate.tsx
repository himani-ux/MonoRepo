import { useState } from 'react';
import { getErrorMessage } from '@/lib/api/client';
import { useSessionReauth } from '@/hooks/use-session-reauth';
import { SessionReauthModal } from './session-reauth-modal';

export function SessionReauthGate() {
  const session = useSessionReauth();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (password: string) => {
    setError(null);
    try {
      await session.reauthenticate(password);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return (
    <SessionReauthModal
      open={session.isReauthRequired}
      identifier={session.identifier}
      isSubmitting={session.isSubmitting}
      error={error}
      onSubmit={handleSubmit}
      onLogout={session.logout}
    />
  );
}

