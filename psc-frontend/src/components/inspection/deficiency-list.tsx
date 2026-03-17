import { useState, useMemo, useCallback, type FC } from 'react';
import { Plus, AlertCircle, Send } from 'lucide-react';
import { Button, Checkbox } from '@/components/ui';
import { EmptyState, ConfirmDialog } from '@/components/shared';
import { DeficiencyCard } from './deficiency-card';
import { useBulkSubmitDeficiencies } from '@/hooks/use-deficiencies';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import type { DeficiencyDetail } from '@/types';

/** Deficiencies with PENDING_MASTER_REVIEW CAR status are eligible for bulk submit */
const BULK_SUBMIT_CAR_STATUS = 'PENDING_MASTER_REVIEW';
/** Deficiencies with APPROVED def_status are selectable for bulk submit */
const APPROVED_STATUS = 'APPROVED';

/**
 * Props for DeficiencyList component
 */
export interface DeficiencyListProps {
  /** Array of deficiencies to display */
  deficiencies: DeficiencyDetail[];
  /** Callback to add a new deficiency (only shown in DRAFT status) */
  onAddDeficiency?: () => void;
  /** Callback when a deficiency card is clicked */
  onDeficiencyClick?: (deficiency: DeficiencyDetail) => void;
  /** Additional class names */
  className?: string;
  /** Enable bulk submit UI (Master only, when APPROVED DEFs exist) */
  bulkSubmitEnabled?: boolean;
  /** Inspection ID for bulk submit */
  inspectionId?: string;
}

/**
 * DeficiencyList displays a list of deficiencies for an inspection.
 * Shows count in header and empty state when no deficiencies.
 * Supports bulk selection and submission of APPROVED deficiencies.
 */
export const DeficiencyList: FC<DeficiencyListProps> = ({
  deficiencies,
  onAddDeficiency,
  onDeficiencyClick,
  className,
  bulkSubmitEnabled,
  inspectionId,
}) => {
  const { toast } = useToast();
  const bulkSubmitMutation = useBulkSubmitDeficiencies();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showBulkConfirm, setShowBulkConfirm] = useState(false);

  const count = deficiencies.length;
  const openCount = deficiencies.filter((d) => !d.is_cleared).length;

  const approvedDeficiencies = useMemo(
    () => deficiencies.filter((d) => d.car?.status === BULK_SUBMIT_CAR_STATUS),
    [deficiencies]
  );
  const approvedCount = approvedDeficiencies.length;
  const allApprovedSelected =
    approvedCount > 0 && approvedDeficiencies.every((d) => selectedIds.has(String(d.id)));

  const toggleSelect = useCallback((id: string, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (allApprovedSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(approvedDeficiencies.map((d) => String(d.id))));
    }
  }, [allApprovedSelected, approvedDeficiencies]);

  const handleBulkSubmit = async () => {
    if (!inspectionId || selectedIds.size === 0) return;
    try {
      await bulkSubmitMutation.mutateAsync({
        inspectionId,
        deficiencyIds: Array.from(selectedIds),
      });
      toast({
        title: 'Deficiencies submitted',
        description: `${selectedIds.size} deficiencies submitted to office.`,
      });
      setSelectedIds(new Set());
      setShowBulkConfirm(false);
    } catch {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to submit deficiencies. Please try again.',
      });
    }
  };

  const showBulkUI = bulkSubmitEnabled && approvedCount > 0;

  return (
    <section className={cn('space-y-3', className)}>
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-base font-semibold text-gray-900">
            DEFICIENCIES ({count})
            {count > 0 && openCount < count && (
              <span className="ml-2 text-sm font-normal text-gray-500">
                {openCount} open
              </span>
            )}
          </h2>
          {showBulkUI && (
            <label
              className="flex items-center gap-1.5 text-sm text-gray-600 cursor-pointer"
              onClick={(e) => e.stopPropagation()}
            >
              <Checkbox
                checked={allApprovedSelected}
                onCheckedChange={toggleSelectAll}
              />
              Select All Approved ({approvedCount})
            </label>
          )}
        </div>
        <div className="flex items-center gap-2">
          {showBulkUI && selectedIds.size > 0 && (
            <Button
              type="button"
              variant="default"
              size="sm"
              onClick={() => setShowBulkConfirm(true)}
              className="gap-1"
            >
              <Send className="h-4 w-4" />
              Submit Selected ({selectedIds.size})
            </Button>
          )}
          {onAddDeficiency && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onAddDeficiency}
              className="gap-1"
            >
              <Plus className="h-4 w-4" />
              Add
            </Button>
          )}
        </div>
      </div>

      {/* Deficiency Cards or Empty State */}
      {count === 0 ? (
        <EmptyState
          icon={AlertCircle}
          title="No deficiencies"
          description="No deficiencies have been recorded for this inspection."
          actionLabel={onAddDeficiency ? 'Add Deficiency' : undefined}
          onAction={onAddDeficiency}
          className="py-8"
        />
      ) : (
        <div className="space-y-3">
          {deficiencies.map((deficiency) => {
            const isApproved = deficiency.def_status === APPROVED_STATUS;
            return (
              <DeficiencyCard
                key={deficiency.id}
                deficiency={deficiency}
                onClick={
                  onDeficiencyClick
                    ? () => onDeficiencyClick(deficiency)
                    : undefined
                }
                selectable={showBulkUI && isApproved}
                selected={selectedIds.has(String(deficiency.id))}
                onSelectChange={(sel) => toggleSelect(String(deficiency.id), sel)}
              />
            );
          })}
        </div>
      )}

      {/* Bulk Submit Confirm Dialog */}
      <ConfirmDialog
        open={showBulkConfirm}
        onOpenChange={setShowBulkConfirm}
        title="Submit Deficiencies to Office"
        description={`Are you sure you want to submit ${selectedIds.size} approved deficiencies to the office? This action cannot be undone.`}
        confirmLabel="Submit All"
        onConfirm={handleBulkSubmit}
        confirmDisabled={bulkSubmitMutation.isPending}
      />
    </section>
  );
};
