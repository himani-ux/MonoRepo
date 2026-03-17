import { useState, type FC } from 'react';
import {
  ChevronDown,
  ChevronUp,
  FileText,
  Camera,
  CheckCircle,
  Send,
  RotateCcw,
  AlertCircle,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui';
import type { ActivityEvent } from '@/types';

export interface ActivityHistoryProps {
  events: ActivityEvent[];
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

/** Map event types to icons */
function getEventIcon(eventType: string) {
  const type = eventType.toUpperCase();
  if (type.includes('CREAT')) return FileText;
  if (type.includes('EVIDENCE') || type.includes('UPLOAD')) return Camera;
  if (type.includes('COMPLETE') || type.includes('ACCEPT') || type.includes('CLOSE'))
    return CheckCircle;
  if (type.includes('SUBMIT')) return Send;
  if (type.includes('REWORK') || type.includes('REOPEN')) return RotateCcw;
  return AlertCircle;
}

export const ActivityHistory: FC<ActivityHistoryProps> = ({
  events,
  className,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex w-full items-center justify-between text-left"
        >
          <h2 className="text-base font-semibold text-gray-900">
            ACTIVITY HISTORY ({events.length})
          </h2>
          {isExpanded ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {isExpanded && events.length > 0 && (
          <div className="mt-3 space-y-3">
            {events.map((event) => {
              const Icon = getEventIcon(event.event_type);
              return (
                <div
                  key={event.id}
                  className="flex items-start gap-3 text-sm"
                >
                  <Icon className="mt-0.5 h-4 w-4 flex-shrink-0 text-gray-400" />
                  <div className="min-w-0">
                    <p className="text-gray-700">{event.event_description}</p>
                    <p className="mt-0.5 text-xs text-gray-400">
                      {event.performed_by_name} &middot;{' '}
                      {formatDateTime(event.performed_at)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {isExpanded && events.length === 0 && (
          <p className="mt-3 text-sm text-gray-500 italic">
            No activity recorded yet
          </p>
        )}
      </CardContent>
    </Card>
  );
};
