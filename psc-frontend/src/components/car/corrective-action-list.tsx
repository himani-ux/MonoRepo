import type { FC } from 'react';
import { Card, CardContent } from '@/components/ui';
import { CorrectiveActionItem } from './corrective-action-item';
import { ACTION_TYPES } from '@/lib/utils/constants';
import type { CorrectiveAction } from '@/types';

export interface CorrectiveActionListProps {
  actions: CorrectiveAction[];
  className?: string;
}

export const CorrectiveActionList: FC<CorrectiveActionListProps> = ({
  actions,
  className,
}) => {
  const immediate = actions
    .filter((a) => a.action_type === ACTION_TYPES.IMMEDIATE)
    .sort((a, b) => a.sequence_no - b.sequence_no);

  const longTerm = actions
    .filter((a) => a.action_type === ACTION_TYPES.LONG_TERM)
    .sort((a, b) => a.sequence_no - b.sequence_no);

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <h2 className="mb-3 text-base font-semibold text-gray-900">
          CORRECTIVE ACTIONS
        </h2>

        {actions.length === 0 ? (
          <p className="text-sm text-gray-500 italic">
            No corrective actions added yet
          </p>
        ) : (
          <div className="space-y-4">
            {/* Immediate Actions */}
            <div>
              <h3 className="mb-2 text-sm font-semibold text-gray-700">
                IMMEDIATE ({immediate.length})
              </h3>
              {immediate.length === 0 ? (
                <p className="text-sm text-gray-400 italic">
                  No immediate actions
                </p>
              ) : (
                <div className="space-y-2">
                  {immediate.map((action, idx) => (
                    <CorrectiveActionItem
                      key={action.id}
                      action={action}
                      index={idx + 1}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Long-term Actions */}
            <div>
              <h3 className="mb-2 text-sm font-semibold text-gray-700">
                LONG-TERM ({longTerm.length})
              </h3>
              {longTerm.length === 0 ? (
                <p className="text-sm text-gray-400 italic">
                  No long-term actions
                </p>
              ) : (
                <div className="space-y-2">
                  {longTerm.map((action, idx) => (
                    <CorrectiveActionItem
                      key={action.id}
                      action={action}
                      index={immediate.length + idx + 1}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
