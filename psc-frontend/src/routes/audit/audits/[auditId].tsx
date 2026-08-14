import { useParams } from 'react-router-dom';
import { AuditDetailPage } from '@/components/audit/audit-detail/audit-detail-page';

export default function AuditDetailRoute() {
  const { auditId } = useParams<{ auditId: string }>();
  return <AuditDetailPage auditId={auditId || ''} />;
}
