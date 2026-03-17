// src/hooks/useReportHandler.js
import { useState, useCallback } from 'react';
import { buildItemRows, formatDate } from '../../utils/orb/orbUtils';
import { useFetchOperationsQuery } from '../../services/orb/orbApi';

export const useReportHandler = (vesselId) => {
  const [reportData, setReportData] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [isReportVisible, setIsReportVisible] = useState(false);

  const { data: allApprovedOps = [] } = useFetchOperationsQuery(
    { vesselId, status: "Approved", isDeleted: false },
    { skip: !vesselId }
  );

  const handleReportPeriod = useCallback(async (period) => {
    console.log("handleReportPeriod called with:", period);

    if (!vesselId) {
      alert("Vessel not selected");
      console.error("No vesselId");
      return;
    }

    setSelectedPeriod(period);
    setIsReportVisible(true);
    setReportData([]);

    const today = new Date();
    let fromDate = new Date();

    switch (period) {
      case 'TM': // This Month
        fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
        break;
      case '1M':
        fromDate.setMonth(today.getMonth() - 1);
        break;
      case '6M':
        fromDate.setMonth(today.getMonth() - 6);
        break;
      case '1Y':
        fromDate.setFullYear(today.getFullYear() - 1);
        break;
      case '3Y':
        fromDate.setFullYear(today.getFullYear() - 3);
        break;
      default:
        fromDate = new Date(0);
    }

    console.log("📅 Date Range:", formatDate(fromDate), "to", formatDate(today));

    try {
      const ops = allApprovedOps;
      console.log("All Approved Entries:", ops);

      if (ops.length === 0) {
        alert("No approved entries found in the system.");
        return;
      }

      // Filter by date
      const filtered = ops.filter(entry => {
        if (!entry.date) {
          console.warn("Entry missing date:", entry);
          return false;
        }

        const entryDate = new Date(entry.date);
        if (isNaN(entryDate)) {
          console.warn("Invalid date format:", entry.date, "for entry:", entry);
          return false;
        }

        const isValid = entryDate >= fromDate && entryDate <= today;
        console.log(`Entry ${entry.id} date:`, formatDate(entry.date), "Valid:", isValid);
        return isValid;
      });

      console.log("Filtered Entries:", filtered);

      if (filtered.length === 0) {
        alert("No approved entries found in the selected period.");
        setReportData([]);
        return;
      }

      // Format with rows
      const formatted = filtered.map(entry => {
        console.log("Entry before buildItemRows:", entry);
        try {
          return {
            ...entry,
            rows: buildItemRows(
              entry.code,
              entry.details,
              entry.date,
              entry.created_by,
              []
            )
          };
        } catch (err) {
          console.error("Failed to build rows for entry:", entry, err);
          return null;
        }
      }).filter(Boolean);

      console.log("📊 Formatted Rows:", formatted);
      setReportData(formatted);

    } catch (err) {
      console.error("Error in handleReportPeriod:", err);
      alert("Network error: Cannot load report. Check console.");
    }
  }, [vesselId, allApprovedOps]);

  const closeReport = () => {
    setIsReportVisible(false);
    setSelectedPeriod(null);
    setReportData([]);
  };

  return {
    reportData,
    selectedPeriod,
    isReportVisible,
    handleReportPeriod,
    closeReport
  };
};
