import { useMemo, type FC } from 'react';
import { FileWarning } from 'lucide-react';
import { Card, CardContent } from '@/components/ui';
import { useCLCItems } from '@/hooks/use-masters';
import type { CarClcMapping } from '@/types';

export interface RootCauseSectionProps {
  rootCauseSummary: string | null;
  clcItems: CarClcMapping[];
  className?: string;
}

export const RootCauseSection: FC<RootCauseSectionProps> = ({
  rootCauseSummary,
  clcItems,
  className,
}) => {
  const { data: masterClcItems } = useCLCItems();
  const hasContent = rootCauseSummary || clcItems.length > 0;
  const clcDisplayMap = useMemo(
    () =>
      Object.fromEntries(
        (masterClcItems ?? []).map((item) => [item.clc_code, item.display_text])
      ),
    [masterClcItems]
  );

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <h2 className="mb-3 text-base font-semibold text-gray-900">
          ROOT CAUSE ANALYSIS
        </h2>

        {!hasContent ? (
          <div className="flex items-center gap-2 text-sm text-gray-500 italic">
            <FileWarning className="h-4 w-4" />
            <span>No root cause analysis provided yet</span>
          </div>
        ) : (
          <div className="space-y-3">
            {/* CLC Codes */}
            {clcItems.length > 0 && (
              <div>
                <p className="mb-1 text-sm font-medium text-gray-700">
                  CLC Codes:
                </p>
                <ul className="space-y-1 pl-4">
                  {clcItems.map((item) => (
                    <li
                      key={item.id}
                      className="list-disc text-sm text-gray-600"
                    >
                      <span className="font-medium">
                        {clcDisplayMap[item.clc_item_id] || item.clc_item_id}
                      </span>
                      {item.custom_cause_text && (
                        <span>: {item.custom_cause_text}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Summary */}
            {rootCauseSummary && (
              <div>
                <p className="mb-1 text-sm font-medium text-gray-700">
                  Summary:
                </p>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">
                  {rootCauseSummary}
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};