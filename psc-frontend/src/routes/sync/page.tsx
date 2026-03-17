/**
 * SyncStatusPage — Sync & Offline management page.
 *
 * Assembles all sync components: connection status, storage indicator,
 * pending changes, conflicts. Provides "Sync Now" and "Clear Old Data" actions.
 *
 * Source: FRONTEND_GUIDELINES.md Section 3
 * Implements: PRD.md FEAT-SYNC-001
 * Flow: APP_FLOW.md Section 2.5
 */

import { useState, useCallback } from 'react';
import { RefreshCw, Trash2 } from 'lucide-react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { Button } from '@/components/ui';
import { ConfirmDialog } from '@/components/shared';
import {
  SyncStatus,
  StorageIndicator,
  PendingChanges,
  ConflictList,
  ConflictResolutionModal,
} from '@/components/sync';
import { useOffline } from '@/hooks/use-offline';
import { useAuth } from '@/hooks/use-auth';
import { useConflicts, useInvalidateConflicts } from '@/hooks/use-sync';
import { useSyncStore } from '@/stores/sync-store';
import { fullSync } from '@/lib/sync/sync-service';
import { clearAllStores } from '@/lib/db';
import { resolveConflict as resolveConflictAPI } from '@/lib/api/sync';
import { useToast } from '@/hooks/use-toast';
import type { SyncConflict } from '@/types';

export default function SyncStatusPage() {
  const { isOnline, lastSyncTime, syncInProgress, pendingChanges, conflicts } =
    useOffline();
  const { lastSyncError } = useSyncStore();
  const { isOffice, isDPA } = useAuth();
  const { toast } = useToast();

  const canResolveConflicts = isOffice || isDPA;

  // Fetch real conflicts from backend when online and conflicts exist
  const { data: conflictItems = [] } = useConflicts(
    isOnline && conflicts > 0
  );
  const invalidateConflicts = useInvalidateConflicts();

  const [selectedConflict, setSelectedConflict] = useState<SyncConflict | null>(null);
  const [conflictModalOpen, setConflictModalOpen] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const [clearing, setClearing] = useState(false);

  // Sync Now handler
  const handleSyncNow = useCallback(async () => {
    if (!isOnline) {
      toast({
        title: 'Offline',
        description: 'Cannot sync while offline. Please connect to the internet.',
        variant: 'destructive',
      });
      return;
    }
    try {
      const result = await fullSync();
      // Refetch conflicts in case new ones were detected during sync
      invalidateConflicts();
      toast({
        title: 'Sync Complete',
        description: `Pulled ${result.pullRecords} records, pushed ${result.pushProcessed} changes.${
          result.conflicts > 0 ? ` ${result.conflicts} conflicts detected.` : ''
        }`,
      });
    } catch (error) {
      toast({
        title: 'Sync Failed',
        description: error instanceof Error ? error.message : 'An error occurred during sync.',
        variant: 'destructive',
      });
    }
  }, [isOnline, invalidateConflicts, toast]);

  // Clear Old Data handler
  const handleClearData = useCallback(async () => {
    setClearing(true);
    try {
      await clearAllStores();
      useSyncStore.getState().resetSyncState();
      setClearDialogOpen(false);
      toast({
        title: 'Data Cleared',
        description: 'All cached data has been removed. Sync to reload.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to clear data. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setClearing(false);
    }
  }, [toast]);

  // Retry failed items
  const handleRetryFailed = useCallback(async () => {
    await handleSyncNow();
  }, [handleSyncNow]);

  // Conflict resolution
  const handleResolveConflict = (conflict: SyncConflict) => {
    setSelectedConflict(conflict);
    setConflictModalOpen(true);
  };

  const handleSubmitResolution = useCallback(
    async (
      conflictId: string,
      resolution: 'KEEP_SERVER' | 'KEEP_VESSEL' | 'REOPEN_FOR_MERGE',
      notes?: string
    ) => {
      setResolving(true);
      try {
        await resolveConflictAPI({
          conflict_id: conflictId,
          resolution,
          notes,
        });
        // Refresh conflict list from server and update count
        useSyncStore.getState().setConflicts(Math.max(0, conflicts - 1));
        invalidateConflicts();
        setConflictModalOpen(false);
        setSelectedConflict(null);
        toast({
          title: 'Conflict Resolved',
          description: `Applied ${resolution.replace(/_/g, ' ').toLowerCase()} resolution.`,
        });
      } catch (error) {
        toast({
          title: 'Resolution Failed',
          description: error instanceof Error ? error.message : 'Failed to resolve conflict.',
          variant: 'destructive',
        });
      } finally {
        setResolving(false);
      }
    },
    [conflicts, invalidateConflicts, toast]
  );

  return (
    <RootLayout>
      <PageHeader title="Sync Status" showBack backTo="/inspections" />

      <div className="space-y-4 pb-24">
        {/* Connection status + last sync */}
        <SyncStatus
          isOnline={isOnline}
          lastSyncTime={lastSyncTime}
          syncInProgress={syncInProgress}
          lastSyncError={lastSyncError}
        />

        {/* Storage usage */}
        <StorageIndicator />

        {/* Pending changes + failed uploads */}
        <PendingChanges
          pendingCount={pendingChanges}
          onRetryFailed={handleRetryFailed}
          retryInProgress={syncInProgress}
        />

        {/* Conflicts */}
        <ConflictList
          conflicts={conflictItems}
          canResolve={canResolveConflicts}
          onResolve={handleResolveConflict}
        />

        {/* Conflict resolution modal */}
        <ConflictResolutionModal
          open={conflictModalOpen}
          onOpenChange={setConflictModalOpen}
          conflict={selectedConflict}
          onResolve={handleSubmitResolution}
          resolving={resolving}
        />

        {/* Clear data confirmation */}
        <ConfirmDialog
          open={clearDialogOpen}
          onOpenChange={setClearDialogOpen}
          title="Clear Cached Data"
          description="This will remove all locally cached inspections, CARs, and attachments. You will need to sync again to reload data. Pending changes will be lost."
          confirmLabel="Clear Data"
          variant="destructive"
          showIcon
          onConfirm={handleClearData}
          confirmDisabled={clearing}
        />
      </div>

      {/* Sticky bottom bar with actions */}
      <div className="fixed bottom-0 left-0 right-0 border-t border-neutral-200 bg-white px-4 py-3 md:left-64">
        <div className="flex items-center gap-3">
          <Button
            onClick={handleSyncNow}
            disabled={syncInProgress || !isOnline}
            className="flex-1"
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${syncInProgress ? 'animate-spin' : ''}`}
            />
            {syncInProgress ? 'Syncing...' : 'Sync Now'}
          </Button>
          <Button
            variant="outline"
            onClick={() => setClearDialogOpen(true)}
            disabled={syncInProgress}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Clear Old Data
          </Button>
        </div>
      </div>
    </RootLayout>
  );
}
