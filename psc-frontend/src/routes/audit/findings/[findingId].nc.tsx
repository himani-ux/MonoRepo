import { useParams } from 'react-router-dom';
import { AuditNcClosurePage } from '@/components/audit/finding/audit-nc-closure-page';

export default function AuditNcClosureRoute() {
  const { findingId } = useParams<{ findingId: string }>();
  return <AuditNcClosurePage findingId={findingId || ''} />;
}
