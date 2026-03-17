// src/hooks/useORBOperations.js
import { useEffect } from 'react';
import { buildItemRows } from '../../utils/orb/orbUtils';
import {
  useFetchOperationsQuery,
  useApproveOperationMutation,
  useRejectOperationMutation,
  useFetchVesselsQuery,
} from '../../services/orb/orbApi';

export const useORBOperations = ({
  vesselId,
  user
}) => {
  // Fetch all operations
  const { data: allOperations = [], refetch: refetchOperations } = useFetchOperationsQuery(
    { vesselId, isDeleted: false },
    { skip: !vesselId }
  );

  // Fetch vessels
  const { data: vessels = [] } = useFetchVesselsQuery();

  // Mutations
  const [approveOp] = useApproveOperationMutation();
  const [rejectOp] = useRejectOperationMutation();

  // Filter and format pending entries
  const pending = allOperations
    .filter(e => e.status === "Pending")
    .map(entry => ({
      ...entry,
      rows: buildItemRows(entry.code, entry.details, entry.date, entry.created_by)
    }))
    .sort((a, b) => {
      if (a.code === "A" && b.code === "B") return -1;
      if (a.code === "B" && b.code === "A") return 1;
      return new Date(a.created_at) - new Date(b.created_at);
    });

  // Filter and format approved entries
  const exportedIds = JSON.parse(localStorage.getItem("exportedApprovedIds") || "[]");
  const approved = allOperations
    .filter(e => e.status === "Approved" && !exportedIds.includes(e.id))
    .map(entry => ({
      ...entry,
      rows: buildItemRows(entry.code, entry.details, entry.date, entry.created_by)
    }))
    .sort((a, b) => {
      if (a.code === "A" && b.code === "B") return -1;
      if (a.code === "B" && b.code === "A") return 1;
      return new Date(a.approved_at) - new Date(b.approved_at);
    });

  // Get vessel info
  const selectedVessel = vessels.find(v => v.id.toLowerCase() === vesselId?.toLowerCase());
  const vessel = selectedVessel ? {
    vesselName: selectedVessel.vesselName,
    imoNumber: selectedVessel.imonumber
  } : null;

  const handleApprove = async (id, approvedBy) => {
    try {
      await approveOp({ id, approvedBy }).unwrap();
      alert("Entry Approved");
      await refetchOperations();
    } catch (err) {
      console.error("Approve error:", err);
      alert("Approve failed: " + (err?.message || JSON.stringify(err)));
    }
  };

  const handleReject = async (id, rejectedBy) => {
    try {
      await rejectOp({ id, rejectedBy }).unwrap();
      alert("Entry rejected");
      await refetchOperations();
    } catch (err) {
      console.error("Reject error:", err);
      alert("Reject failed: " + (err?.message || JSON.stringify(err)));
    }
  };

  return {
    pending,
    approved,
    vessel,
    setApproved: () => {}, // No-op for compatibility
    refresh: refetchOperations,
    handleApprove,
    handleReject,
  };
};
