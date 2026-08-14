import { useParams } from 'react-router-dom';
import { AuditChecklistWalkPage } from '@/components/audit/checklist/audit-checklist-walk-page';

export default function AuditChecklistRoute() {
  const { auditId } = useParams<{ auditId: string }>();
  return <AuditChecklistWalkPage auditId={auditId || ''} />;
}
