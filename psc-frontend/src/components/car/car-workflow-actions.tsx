/**
 * Unified workflow action buttons for a CAR detail page.
 *
 * Uses the backend available-actions endpoint to determine which
 * actions the current user can take. Shows a comment dialog for
 * actions that require mandatory comments.
 */

import { type FC, useState } from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Textarea,
} from '@/components/ui';
import { useCARAvailableActions, useTransitionCAR, useCAR } from '@/hooks/use-cars';
import { useAuth } from '@/hooks/use-auth';
import { useQueryClient } from '@tanstack/react-query';
import { validateCarSubmission } from '@/lib/validations/car';
import { CAR_STATUS, USER_ROLES, WORKFLOW_ACTIONS } from '@/lib/utils/constants';
import type { AvailableAction } from '@/types';

const CLIENT_REQUIRED_COMMENT_ACTIONS = new Set<string>([
  WORKFLOW_ACTIONS.RETURN_FOR_REWORK,
  WORKFLOW_ACTIONS.SUBMIT_TO_DPA,
  WORKFLOW_ACTIONS.CLOSE_CAR,
  WORKFLOW_ACTIONS.REOPEN_CAR,
  WORKFLOW_ACTIONS.REQUEST_REWORK,
  'SUBMIT_TO_LEAD_AUDITOR',
  'LEAD_AUDITOR_CLOSE',
  'AWAIT_EXTERNAL_CLOSE_OUT',
  'CONFIRM_EXTERNAL_CLOSE',
]);

const actionRequiresComment = (action: AvailableAction | null): boolean => {
  if (!action) return false;
  return Boolean(action.comment_required) || CLIENT_REQUIRED_COMMENT_ACTIONS.has(action.action);
};

export interface CARWorkflowActionsProps {
  carId: string | number;
  onTransitioned?: () => void;
}

export const CARWorkflowActions: FC<CARWorkflowActionsProps> = ({
  carId,
  onTransitioned,
}) => {
  const queryClient = useQueryClient();
  const { role } = useAuth();
  const { data: actions = [] } = useCARAvailableActions(carId);
  const { data: car } = useCAR(carId);
  const transitionMutation = useTransitionCAR(carId);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [masterSubmitToPicAction, setMasterSubmitToPicAction] = useState<AvailableAction | null>(null);
  const [masterSubmitToPicComment, setMasterSubmitToPicComment] = useState('');
  const [picConfirmAction, setPicConfirmAction] = useState<AvailableAction | null>(null);
  const [picConfirmComment, setPicConfirmComment] = useState('');
  const [commentDialogAction, setCommentDialogAction] = useState<AvailableAction | null>(null);
  const [comment, setComment] = useState('');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [showValidationDialog, setShowValidationDialog] = useState(false);
  const masterSendToPicActionAllowlist = new Set([
    WORKFLOW_ACTIONS.SUBMIT_TO_PIC,
    'RESUBMIT_TO_PIC',
    'SUBMIT_TO_PIC_AFTER_REWORK',
  ]);

  const picActionAllowlist = new Set([
    WORKFLOW_ACTIONS.START_PIC_REVIEW,
    WORKFLOW_ACTIONS.SUBMIT_TO_DPA,
    WORKFLOW_ACTIONS.REQUEST_REWORK,
    'ACCEPT_AND_FORWARD_TO_DPA',
  ]);
  const picStates: ReadonlySet<string> = new Set([
    CAR_STATUS.SUBMITTED_TO_PIC,
    CAR_STATUS.PIC_REVIEW,
  ]);
  const isPICRole =
    role === USER_ROLES.OFFICE_PIC ||
    role === USER_ROLES.OFFICE_SSQE ||
    role === USER_ROLES.OFFICE_SUPT;

  if (actions.length === 0) return null;

  const isPICAction = (action: AvailableAction): boolean => {
    const actionRole = (action as AvailableAction & { role?: string }).role;
    if (typeof actionRole === 'string' && actionRole.toUpperCase() === 'PIC') {
      return true;
    }
    if (picActionAllowlist.has(action.action)) {
      return true;
    }
    return Boolean(car?.status && picStates.has(car.status));
  };

  const shouldConfirmPICAction = (action: AvailableAction): boolean => {
    return isPICRole && isPICAction(action);
  };

  const isPICCommentRequired = (action: AvailableAction | null): boolean => {
    return actionRequiresComment(action);
  };

  const isMasterSubmitToPICAction = (action: AvailableAction): boolean => {
    return (
      role === USER_ROLES.VESSEL_MASTER &&
      masterSendToPicActionAllowlist.has(action.action)
    );
  };

  const handleAction = async (action: AvailableAction) => {
    // Client-side validation gate for SUBMIT_TO_PIC
    if (action.action === WORKFLOW_ACTIONS.SUBMIT_TO_PIC && car) {
      const clcItemIds = car.clc_items
        .map((c) => c.clc_item_id)
        .filter(Boolean);
      const customCauseText =
        car.clc_items.find((c) => c.custom_cause_text)?.custom_cause_text ?? null;

      const result = validateCarSubmission(
        car.root_cause_summary,
        clcItemIds,
        customCauseText,
        car.corrective_actions,
        car.evidence
      );

      if (!result.valid) {
        setValidationErrors(result.errors);
        setShowValidationDialog(true);
        return;
      }
    }

    if (shouldConfirmPICAction(action)) {
      setPicConfirmAction(action);
      setPicConfirmComment('');
      return;
    }
    if (isMasterSubmitToPICAction(action)) {
      setMasterSubmitToPicAction(action);
      setMasterSubmitToPicComment('');
      return;
    }

    if (actionRequiresComment(action)) {
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
        comment: actionComment?.trim() || '',
      });
      queryClient.invalidateQueries({ queryKey: ['cars'] });
      onTransitioned?.();
    } finally {
      setPendingAction(null);
      setMasterSubmitToPicAction(null);
      setMasterSubmitToPicComment('');
      setPicConfirmAction(null);
      setPicConfirmComment('');
      setCommentDialogAction(null);
      setComment('');
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
          onClick={() => handleAction(action)}
        >
          {pendingAction === action.action && (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          )}
          {action.label}
        </Button>
      ))}

      {/* Master confirmation dialog for submit/resubmit to PIC */}
      <Dialog
        open={!!masterSubmitToPicAction}
        onOpenChange={(open) => {
          if (!open) {
            setMasterSubmitToPicAction(null);
            setMasterSubmitToPicComment('');
          }
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Confirm submission</DialogTitle>
            <DialogDescription>
              Send this CAR back to PIC for review?
            </DialogDescription>
          </DialogHeader>
          {actionRequiresComment(masterSubmitToPicAction) && (
            <div className="py-2">
              <Textarea
                placeholder="Enter your comment (required)..."
                value={masterSubmitToPicComment}
                onChange={(e) => setMasterSubmitToPicComment(e.target.value)}
                rows={3}
              />
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setMasterSubmitToPicAction(null);
                setMasterSubmitToPicComment('');
              }}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button
              disabled={
                isPending ||
                (actionRequiresComment(masterSubmitToPicAction) && !masterSubmitToPicComment.trim())
              }
              onClick={() => {
                if (masterSubmitToPicAction) {
                  executeTransition(masterSubmitToPicAction.action, masterSubmitToPicComment);
                }
              }}
            >
              {isPending && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* PIC confirmation dialog */}
      <Dialog
        open={!!picConfirmAction}
        onOpenChange={(open) => {
          if (!open) {
            setPicConfirmAction(null);
            setPicConfirmComment('');
          }
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Confirm Action</DialogTitle>
            <DialogDescription>
              Are you sure you want to {picConfirmAction?.label}?
            </DialogDescription>
          </DialogHeader>
          {isPICCommentRequired(picConfirmAction) && (
            <div className="py-2">
              <Textarea
                placeholder="Enter PIC comment (required)..."
                value={picConfirmComment}
                onChange={(e) => setPicConfirmComment(e.target.value)}
                rows={3}
              />
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setPicConfirmAction(null);
                setPicConfirmComment('');
              }}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button
              disabled={
                isPending ||
                (isPICCommentRequired(picConfirmAction) && !picConfirmComment.trim())
              }
              onClick={() => {
                if (picConfirmAction) {
                  executeTransition(picConfirmAction.action, picConfirmComment);
                }
              }}
            >
              {isPending && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Comment dialog for mandatory-comment actions */}
      <Dialog
        open={!!commentDialogAction}
        onOpenChange={(open) => !open && setCommentDialogAction(null)}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{commentDialogAction?.label}</DialogTitle>
            <DialogDescription className="sr-only">
              A workflow comment is required before this action can be submitted.
            </DialogDescription>
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
