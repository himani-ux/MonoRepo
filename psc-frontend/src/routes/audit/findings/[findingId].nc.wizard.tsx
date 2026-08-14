import { useParams } from 'react-router-dom';
import { AuditNcWizard } from '@/components/audit/finding/audit-nc-wizard';

export default function AuditNcWizardRoute() {
  const { findingId } = useParams<{ findingId: string }>();
  return <AuditNcWizard findingId={findingId || ''} />;
}
