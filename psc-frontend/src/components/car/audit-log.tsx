import { useState, type FC } from 'react';
import { History, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent } from '@/components/ui';
import type { AuditLogEntry } from '@/types';

export interface AuditLogProps {
  entries: AuditLogEntry[];
  className?: string;
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export const AuditLog: FC<AuditLogProps> = ({ entries, className }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (entries.length === 0) return null;

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex w-full items-center justify-between text-left"
        >
          <h2 className="text-base font-semibold text-gray-900">
            AUDIT LOG ({entries.length})
          </h2>
          {isExpanded ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {isExpanded && (
          <div className="mt-3 space-y-3">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="rounded-md border border-neutral-200 bg-neutral-50 p-3 text-sm"
              >
                <div className="flex items-start gap-2">
                  <History className="mt-0.5 h-4 w-4 flex-shrink-0 text-gray-400" />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-700">
                      {entry.action === 'UPDATE'
                        ? `Field changed: ${entry.field_name}`
                        : `${entry.action}: ${entry.field_name}`}
                    </p>
                    {entry.old_value !== null && (
                      <p className="mt-1 text-xs text-gray-500">
                        <span className="text-error-600">Old:</span>{' '}
                        {entry.old_value || '(empty)'}
                      </p>
                    )}
                    {entry.new_value !== null && (
                      <p className="text-xs text-gray-500">
                        <span className="text-success-600">New:</span>{' '}
                        {entry.new_value || '(empty)'}
                      </p>
                    )}
                    <p className="mt-1 text-xs text-gray-400">
                      By: {entry.performed_by_role}
                      {entry.is_office_edit_assist && ' (Edit Assist)'}
                      {' · '}
                      {formatDateTime(entry.performed_at)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
