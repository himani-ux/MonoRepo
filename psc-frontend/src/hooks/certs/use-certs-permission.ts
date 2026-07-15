import { useMemo } from 'react';

import { useAuth } from '@/hooks/use-auth';
import { FORM_IDS } from '@/lib/utils/permission-ids';

const CERTS_FORM_IDS = [
  FORM_IDS.CERTS_CATALOG,
  FORM_IDS.CERTS_TRACKED_ITEMS,
  FORM_IDS.CERTS_RECONCILIATION,
  FORM_IDS.CERTS_PRINT_EXPORT,
  FORM_IDS.CERTS_ONBOARDING,
  FORM_IDS.CERTS_NOTIFICATION_CONFIG,
  FORM_IDS.CERTS_AUDITOR_ACCESS,
  FORM_IDS.CERTS_AUDIT_LOG,
] as const;

export function useCertsPermission(formId?: string, processId?: string): boolean {
  const { hasForm, hasProcess } = useAuth();

  return useMemo(() => {
    if (formId && !hasForm(formId)) {
      return false;
    }

    if (processId && !hasProcess(processId)) {
      return false;
    }

    if (!formId && !processId) {
      return CERTS_FORM_IDS.some((certsFormId) => hasForm(certsFormId));
    }

    return true;
  }, [formId, hasForm, hasProcess, processId]);
}

export function useHasAnyCertsForm(): boolean {
  return useCertsPermission();
}

export { CERTS_FORM_IDS };
