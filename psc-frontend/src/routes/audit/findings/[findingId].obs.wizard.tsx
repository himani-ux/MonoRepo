import { useParams } from 'react-router-dom';
import { AuditObsClosurePage } from '@/components/audit/finding/audit-obs-closure-page';

export default function AuditObsWizardRoute() {
  const { findingId } = useParams<{ findingId: string }>();
  return <AuditObsClosurePage findingId={findingId || ''} mode="wizard" />;
}
