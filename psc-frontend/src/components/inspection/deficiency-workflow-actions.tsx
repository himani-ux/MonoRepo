/**
 * Context-sensitive workflow action buttons for a deficiency.
 *
 * Uses the unified CAR workflow: buttons are driven by car.status + user role.
 * Calls the transitionCAR() API with named actions.
 * Shows a comment dialog for actions that require mandatory comments.
 */

import { type FC, useState } from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Textarea,
} from '@/components/ui';
import { useTransitionCAR, useCARAvailableActions } from '@/hooks/use-cars';
import { useQueryClient } from '@tanstack/react-query';
import type { DeficiencyDetail, AvailableAction } from '@/types';

export interface DeficiencyWorkflowActionsProps {
  deficiency: DeficiencyDetail;
  onTransitioned?: () => void;
}

export const DeficiencyWorkflowActions: FC<DeficiencyWorkflowActionsProps> = ({
  deficiency,
  onTransitioned,
}) => {
  const queryClient = useQueryClient();
  const carId = deficiency.car?.id;
  const transitionMutation = useTransitionCAR(carId || 0);
  const { data: actions = [] } = useCARAvailableActions(carId);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [commentDialogAction, setCommentDialogAction] = useState<AvailableAction | null>(null);
  const [comment, setComment] = useState('');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [showValidationDialog, setShowValidationDialog] = useState(false);

  if (!carId) return null;

  const carStatus = deficiency.car?.status;
  if (!carStatus) return null;
  if (actions.length === 0) return null;

  const handleAction = async (action: AvailableAction) => {
    if (action.comment_required) {
      setCommentDialogAction(action);
      setComment('');
      return;
    }
    await executeTransition(action.action);
  };

  const executeTransition = async (actionName: string, actionComment?: string) => {
    setPendingAction(actionName);
    try {
      await transitionMutation.mutateAsync({
        action: actionName,
        comment: actionComment || '',
      });
      queryClient.invalidateQueries({ queryKey: ['deficiencies'] });
      onTransitioned?.();
    } catch (err: unknown) {
      // Handle backend validation errors (e.g. SUBMIT_TO_PIC on incomplete CAR)
      const error = err as { response?: { data?: { error?: string; validation_errors?: Record<string, string> } } };
      if (error?.response?.data?.error === 'VALIDATION_ERROR' && error.response.data.validation_errors) {
        const errors = Object.values(error.response.data.validation_errors);
        setValidationErrors(errors);
        setShowValidationDialog(true);
      }
      // Don't re-throw — mutateAsync already updates mutation error state
    } finally {
      setPendingAction(null);
      setCommentDialogAction(null);
    }
  };

  const isPending = transitionMutation.isPending;

  const getVariant = (action: string): 'default' | 'outline' | 'destructive' => {
    if (action.includes('REWORK') || action === 'REOPEN_CAR') return 'outline';
    return 'default';
  };

  return (
    <>
      {actions.map((action) => (
        <Button
          key={action.action}
          size="sm"
          variant={getVariant(action.action)}
          disabled={isPending}
          onClick={(e) => {
            e.stopPropagation();
            handleAction(action);
          }}
        >
          {pendingAction === action.action && (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          )}
          {action.label}
        </Button>
      ))}

      {/* Comment dialog for mandatory-comment actions */}
      <Dialog
        open={!!commentDialogAction}
        onOpenChange={(open) => !open && setCommentDialogAction(null)}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{commentDialogAction?.label}</DialogTitle>
          </DialogHeader>
          <div className="py-2">
            <Textarea
              placeholder="Enter your comment (required)..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCommentDialogAction(null)}
            >
              Cancel
            </Button>
            <Button
              disabled={!comment.trim() || isPending}
              onClick={() => {
                if (commentDialogAction) {
                  executeTransition(commentDialogAction.action, comment);
                }
              }}
            >
              {isPending && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Validation error dialog */}
      <Dialog
        open={showValidationDialog}
        onOpenChange={setShowValidationDialog}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Cannot Submit CAR
            </DialogTitle>
          </DialogHeader>
          <div className="py-2">
            <p className="text-sm text-muted-foreground mb-3">
              Please fix the following issues before submitting:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              {validationErrors.map((err, i) => (
                <li key={i} className="text-sm text-destructive">
                  {err}
                </li>
              ))}
            </ul>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowValidationDialog(false)}>
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
