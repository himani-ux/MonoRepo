import type { AuthUser } from '@/lib/api/auth';
import { ROUTES } from '@/lib/utils/constants';
import { FORM_IDS } from '@/lib/utils/permission-ids';

type CertsNavigationAuth = {
  user: AuthUser | null;
  vesselId?: string | null;
  hasForm: (formId: string) => boolean;
};

export function getCertsVesselIdentifier(auth: Pick<CertsNavigationAuth, 'user' | 'vesselId'>): string {
  return String(auth.vesselId ?? auth.user?.vessel_id ?? auth.user?.vessel_code ?? '').trim();
}

export function getCertsHomeRoute(auth: CertsNavigationAuth): string {
  const canReadCatalog = auth.hasForm(FORM_IDS.CERTS_CATALOG);
  const canReadTrackedItems = auth.hasForm(FORM_IDS.CERTS_TRACKED_ITEMS);
  const vesselIdentifier = getCertsVesselIdentifier(auth);

  if (!canReadCatalog && canReadTrackedItems && vesselIdentifier) {
    return ROUTES.CERTS_VESSEL_DASHBOARD(vesselIdentifier);
  }

  return ROUTES.CERTS;
}
