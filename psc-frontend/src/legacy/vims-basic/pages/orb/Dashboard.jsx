import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { buildItemRows } from "../../utils/orb/orbUtils";
import { useAuth } from "../../hooks/auth/useAuth";
import { useORBHelpers } from "../../hooks/orb/useORBHelpers";
import { useORBValidation } from "../../hooks/orb/useORBValidation";
import { useReportHandler } from "../../hooks/orb/useReportHandler";
import { usePDFGenerator } from "../../hooks/orb/usePDFGenerator";
import {
  useFetchOperationsQuery,
  useFetchCodesQuery,
  useFetchTanksForOrbQuery,
  useFetchLatestEntryDateQuery,
  useFetchVesselsQuery,
  useCreateOperationMutation,
  useUpdateOperationMutation,
  useDeleteOperationMutation,
  useApproveOperationMutation,
  useRejectOperationMutation,
} from "../../services/orb/orbApi";
import { Panel, Stack, Card } from "../../components/orb/OrbUI";
import PageLayout from "../../components/layout/PageLayout";
import "../../styles/orb/CrewDashboard.css";
import "../../styles/orb/orb-theme.css";
import ORBEntryForm from "../../components/orb/ORBEntryForm";
import ORBTable from "../../components/orb/ORBTable";
import ReportFilter from "../../components/orb/ReportFilter";
import ReportView from "../../components/orb/ReportView";
import PendingEntriesCard from "../../components/orb/PendingEntriesCard";
import ApprovedEntriesCard from "../../components/orb/ApprovedEntriesCard";

// ─── Constants ────────────────────────────────────────────────────────────────
const EMPTY_FORM = {
  code: "",
  details: {
    fuel_quantity: "",
    fuel_type: "",
    fuel_tanks: [],
    fuel_sulfur: "",
    fuel_quantities: [],
    fuel_current_contents: [],
    lube_quantity: "",
    lube_type: "",
    lube_tanks: [],
    lube_quantities: [],
    lube_current_contents: [],
    place_of_bunkering: "",
    start_time: "",
    end_time: "",
  },
};

// Form and Process IDs
const FORM_IDS = {
  ENTRY_FORM: "PSC_F_014", // form id for the ORB entry form
  TABLE: "PSC_F_015", // form id for the ORB table
  REPORT_FILTER: "PSC_F_018", // form id for the report filter
  REPORT_VIEW: "PSC_F_019", // form id for the report view
  PENDING_ENTRIES: "PSC_F_016", //form id for pending entries view
  APPROVED_ENTRIES: "PSC_F_017", //form id for approved entries view
};
const PROCESS_IDS = {
  SELECT_CODE: "PSC_P_043", // process id for selecting code in entry form
  EDIT_DRAFT: "PSC_P_037", // process id for editing draft
  DELETE_DRAFT: "PSC_P_038", // process id for deleting draft
  FILTER_REPORTS: "PSC_P_039", // process id for filtering reports
  APPROVE: "PSC_P_040", // process id for approving entry
  REJECT: "PSC_P_041", // process id for rejecting entry
  SAVE_PDF: "PSC_P_042", // process id for saving approved entry as PDF
};

const normalizePermissionId = (id, type) => {
  const normalized = String(id || '').trim().toUpperCase();
  if (!normalized) return '';

  if (type === 'form') {
    if (normalized.startsWith('PSC_F_')) return normalized;
    if (normalized.startsWith('F_')) return `PSC_${normalized}`;
    return normalized;
  }

  if (normalized.startsWith('PSC_P_')) return normalized;
  if (normalized.startsWith('P_')) return `PSC_${normalized}`;
  return normalized;
};

// ─── Component ────────────────────────────────────────────────────────────────
export default function Dashboard() {
  // ── Auth & vessel ───────────────────────────────────────────────────────────
  const { user } = useAuth();

  const vesselId = user?.vessel_id;
  const formIds = user?.form_ids;
  const processIds = user?.process_ids;

  const hasFormAccess = (formId) =>
    (formIds ?? [])
      .map((id) => normalizePermissionId(id, 'form'))
      .includes(normalizePermissionId(formId, 'form'));

const hasProcessAccess = (formId, processId) =>
  (formIds ?? [])
    .map((id) => normalizePermissionId(id, 'form'))
    .includes(normalizePermissionId(formId, 'form')) &&
  (processIds ?? [])
    .map((id) => normalizePermissionId(id, 'process'))
    .includes(normalizePermissionId(processId, 'process'));


  const canAccessEntryForm = hasFormAccess(FORM_IDS.ENTRY_FORM);

  const canAccessTable = hasFormAccess(FORM_IDS.TABLE);
  const canAccessReportFilter = hasFormAccess(FORM_IDS.REPORT_FILTER);
  const canAccessReportView = hasFormAccess(FORM_IDS.REPORT_VIEW);
  const canAccessPendingEntries = hasFormAccess(FORM_IDS.PENDING_ENTRIES);
  const canAccessApprovedEntries = hasFormAccess(FORM_IDS.APPROVED_ENTRIES);
  const canAccessSelectCode = hasProcessAccess(
  FORM_IDS.ENTRY_FORM,
  PROCESS_IDS.SELECT_CODE
);

  const canAccessTableEdit = hasProcessAccess(
    FORM_IDS.TABLE,
    PROCESS_IDS.EDIT_DRAFT,
    
  );
  const canAccessTableDelete = hasProcessAccess(
    FORM_IDS.TABLE,
    PROCESS_IDS.DELETE_DRAFT,
    
  );
  const canAccessFilterReports = hasProcessAccess(
    FORM_IDS.REPORT_FILTER,
    PROCESS_IDS.FILTER_REPORTS,
  );
  const canAccessApprove = hasProcessAccess(FORM_IDS.PENDING_ENTRIES, PROCESS_IDS.APPROVE);
  const canAccessReject = hasProcessAccess(FORM_IDS.PENDING_ENTRIES, PROCESS_IDS.REJECT);
  const canAccessSavePDF = hasProcessAccess(
    FORM_IDS.APPROVED_ENTRIES,
    PROCESS_IDS.SAVE_PDF,
  );

  const navigate = useNavigate();

  // ── Form state ──────────────────────────────────────────────────────────────
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [pendingFEntry, setPendingFEntry] = useState(null);
  const [editingEntryId, setEditingEntryId] = useState(null);

  // ── RTK Query Hooks ─────────────────────────────────────────────────────────
  // Fetch codes
  const { data: codes = [] } = useFetchCodesQuery();

  // Fetch tanks for current code
  const { data: availableTanks = [] } = useFetchTanksForOrbQuery(
    { vesselId, orbCode: formData.code },
    { skip: !vesselId || !formData.code },
  );

  // Fetch all operations (for draft entries)
  const { data: allOperations = [], refetch: refetchOperations } =
    useFetchOperationsQuery(
      { vesselId, isDeleted: false },
      { skip: !vesselId },
    );

    console.log("Fetched all operations for validation:", allOperations);

 

  // Fetch latest entry date
  const { data: latestEntryDate } = useFetchLatestEntryDateQuery(
    { vesselId },
    { skip: !vesselId },
  );

  // Fetch vessels
  const { data: vessels = [] } = useFetchVesselsQuery();

  // Mutations
  const [createOp] = useCreateOperationMutation();
  const [updateOp] = useUpdateOperationMutation();
  const [deleteOp] = useDeleteOperationMutation();
  const [approveOp] = useApproveOperationMutation();
  const [rejectOp] = useRejectOperationMutation();

  // Get vessel info
  const vessel = useMemo(() => {
    const selectedVessel = vessels.find(
      (v) => v.id?.toLowerCase() === vesselId?.toLowerCase(),
    );
    return selectedVessel
      ? {
          vesselName: selectedVessel.vesselName,
          imoNumber: selectedVessel.imonumber,
        }
      : null;
  }, [vessels, vesselId]);


  
  const chiefPending = useMemo(() => {
    return allOperations
      .filter((e) => e.status === "Pending")
      .map((entry) => ({
        ...entry,
        rows: buildItemRows(
          entry.code,
          entry.details,
          entry.date,
          entry.created_by,
        ),
      }))
      .sort((a, b) => {
        if (a.code === "A" && b.code === "B") return -1;
        if (a.code === "B" && b.code === "A") return 1;
        return new Date(a.created_at) - new Date(b.created_at);
      });
  }, [allOperations]);

  console.log("Processed chief pending entries for display:", chiefPending);

    


  //--------------------version 2 -----------------------

  const chiefApproved = useMemo(() => {
  return allOperations
    .filter((e) => e.status === "Approved" && e.master_print === null)
    .map((entry) => ({
      ...entry,
      rows: buildItemRows(
        entry.code,
        entry.details,
        entry.date,
        entry.created_by,
      ),
    }))
    .sort((a, b) => {
      if (a.code === "A" && b.code === "B") return -1;
      if (a.code === "B" && b.code === "A") return 1;
      return new Date(a.created_at) - new Date(b.created_at);
    });
}, [allOperations]);

  console.log("Processed chief approved entries for display:", chiefApproved);

  // ── Helpers & validation ────────────────────────────────────────────────────
  const {
    formatToDateTimeLocal,
    yesterdayDate,
    getSpecialAreaFromPosition,
    buildPosition,
  } = useORBHelpers();

  // ── Report handler ──────────────────────────────────────────────────────────
  const {
    reportData,
    selectedPeriod,
    isReportVisible,
    handleReportPeriod,
    closeReport,
  } = useReportHandler(vesselId);

  // ── PDF generator ───────────────────────────────────────────────────────────
  const { generatePDF } = usePDFGenerator();

  // ── Validation hooks ────────────────────────────────────────────────────────
  const {
    validateCodeA,
    validateCodeB,
    validateCodeC,
    validateCodeD,
    validateCodeF,
    validateCodeG,
    validateCodeI,
  } = useORBValidation({
    availableTanks,
    getSpecialAreaFromPosition,
    buildPosition,
  });

  // ── Effects ─────────────────────────────────────────────────────────────────

  // ── Handlers ────────────────────────────────────────────────────────────────
  const handleChange = (field, value) => {
    // Reset bunkering type when code changes away from H
    if (field === "code" && value !== "H") {
      setFormData((prev) => ({
        ...prev,
        code: value,
        details: { ...prev.details, bunkering_type: "" },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        details: { ...prev.details, [field]: value },
      }));
    }
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: "" }));
  };

  // ── Submit ──────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.code) {
      alert("Please select an operation code (A-I)");
      return;
    }
    if (!vesselId) {
      alert("Vessel not selected");
      return;
    }
    if (!availableTanks?.length) {
      alert("Tank data not loaded. Please wait or refresh.");
      return;
    }

    // Date validation against last entry
    if (latestEntryDate && formData.date) {
      if (new Date(formData.date) < new Date(latestEntryDate)) {
        alert(
          `Entry date cannot be earlier than last entry (${latestEntryDate}).`,
        );
        return;
      }
    }

    // Per-code validation using all operations data
    let validationError = null;
    switch (formData.code) {
      case "A":
        validationError = validateCodeA(formData.details);
        break;
      case "B":
        validationError = validateCodeB(formData.details, allOperations);
        break;
      case "C":
        validationError = validateCodeC(formData.details, allOperations);
        break;
      case "D":
        validationError = validateCodeD(formData.details);
        break;
      case "F":
        validationError = validateCodeF(formData.details);
        break;
      case "G":
        validationError = validateCodeG(formData.details);
        break;
      case "I":
        validationError = validateCodeI(formData.details);
        break;
    }
    if (validationError) {
      alert(`Validation Failed:\n\n${validationError}`);
      return;
    }

    // Build payload
    const orbCode = codes.find((c) => c.code === formData.code);
    if (!orbCode) {
      alert("Invalid ORB Code selected");
      return;
    }

    const rows = buildItemRows(
      formData.code,
      formData.details,
      new Date().toISOString(),
      user,
      availableTanks,
    );
    if (!rows?.length) {
      alert("No operation entries to save");
      return;
    }

    const officerFullName = `${user?.first_name || "OFFICER-IN-CHARGE"} ${
      user?.surname || ""
    }`.trim();

    const payload = {
      vessel: vesselId,
      date: formData.date,
      code: formData.code,
      orb_code_id: orbCode.id,
      item_no: rows[0]?.item || null,
      record_of_operation: rows.map((r) => r.value).join("\n"),
      status: "Pending",
      created_by: officerFullName,
      submitted_by: officerFullName,
      submitted_at: new Date().toISOString(),
      is_deleted: false,
      approved_by: null,
      approved_at: null,
      rejected_by: null,
      rejected_at: null,
    };

    // Edit mode
    if (editingEntryId) {
      try {
        await updateOp({ id: editingEntryId, payload }).unwrap();
        setFormData(EMPTY_FORM);
        setEditingEntryId(null);
        refetchOperations();
        alert("ORB Entry Updated Successfully!");
      } catch (err) {
        alert(`Error updating entry: ${err?.message || JSON.stringify(err)}`);
      }
      return;
    }

    // Code F → mandatory Code I flow
    if (formData.code === "F") {
      setPendingFEntry({ ...payload, details: formData.details });
      alert("Now please add a mandatory Code I to save this entry.");
      setFormData({ code: "I", details: { remarks: "" } });
      return;
    }

    // Code I after pending F
    if (formData.code === "I" && pendingFEntry) {
      const err2 = validateCodeI(formData.details);
      if (err2) {
        alert(`Validation Failed:\n\n${err2}`);
        return;
      }
      try {
        await createOp(pendingFEntry).unwrap();
        await createOp(payload).unwrap();
        alert("Both Code F and Code I entries saved successfully.");
        setPendingFEntry(null);
        setFormData(EMPTY_FORM);
        refetchOperations();
      } catch (err) {
        alert(`Save failed: ${err?.message || JSON.stringify(err)}`);
      }
      return;
    }

    // Normal save
    try {
      await createOp(payload).unwrap();
      alert("ORB Entry Saved");
      setFormData(EMPTY_FORM);
      refetchOperations();
    } catch (err) {
      alert(`Save failed: ${err?.message || JSON.stringify(err)}`);
    }
  };

  // ── Edit ────────────────────────────────────────────────────────────────────
  const handleEdit = (id) => {
    const entry = chiefPending.find((e) => e.id === id);
    if (!entry) {
      alert("Entry not found for editing.");
      return;
    }
    // Simple reconstruction — complex fields may need backend details endpoint
    setFormData({ code: entry.code, details: {} });
    setEditingEntryId(id);
  };

  // ── Delete ──────────────────────────────────────────────────────────────────
  const handleDelete = async (id) => {
    try {
      await deleteOp(id).unwrap();
      alert("Draft deleted successfully");
      refetchOperations();
    } catch (err) {
      alert(`Delete failed: ${err?.message || JSON.stringify(err)}`);
    }
  };

  // ── Chief handlers ──────────────────────────────────────────────────────────
  const doApprove = async (id) => {
    const approvedBy = `${user?.first_name || "UNKNOWN"} ${
      user?.surname || ""
    } (${user?.rank || "OFFICER"})`.trim();
    try {
      await approveOp({ id, approvedBy }).unwrap();
      alert("Entry Approved");
      refetchOperations();
    } catch (err) {
      console.error("Approve error:", err);
      alert("Approve failed: " + (err?.message || JSON.stringify(err)));
    }
  };

  const doReject = async (id) => {
    const rejectedBy = `${user?.first_name || "UNKNOWN"} ${
      user?.surname || ""
    } (${user?.rank || "OFFICER"})`.trim();
    try {
      await rejectOp({ id, rejectedBy }).unwrap();
      alert("Entry rejected");
      refetchOperations();
    } catch (err) {
      console.error("Reject error:", err);
      alert("Reject failed: " + (err?.message || JSON.stringify(err)));
    }
  };

  const handleSavePDF = async () => {
    await generatePDF(chiefApproved, vessel, user, vesselId, () => {
      refetchOperations();
      console.log(
        "✅ UI state updated after Master's successful print and DB update.",
      );
    });
  };



  const navbar = (
  <div className="flex items-center gap-6 text-sm">
    {/* Vessel Info */}
    <div className="text-right leading-tight">
      {vessel ? (
        <>
          <div className="font-semibold tracking-wide text-gray-800">
            {vessel.vesselName?.toUpperCase() || "UNKNOWN VESSEL"}
          </div>
          <div className="text-xs text-gray-500">
            IMO: {vessel.imoNumber || "N/A"}
          </div>
        </>
      ) : (
        <span className="text-gray-400">Vessel Not Found</span>
      )}
    </div>

    {/* Navigation Links */}
    <div className="flex gap-2 border-l border-gray-300 pl-6">
      {[
        { label: "Approved", path: "/orb/approved-entries" },
        { label: "Rejected", path: "/orb/rejected-entries" },
        { label: "Deleted", path: "/orb/deleted-entries" },
        { label: "PDFs", path: "/orb/pdf-archive" },
        { label: "Guidelines", path: "/orb/orb-guidelines" },
      ].map((item) => (
        <button
          key={item.path}
          onClick={() => navigate(item.path)}
          className="
            px-3 py-1.5
            rounded-md
            text-blue-600
            transition-all duration-200
            hover:bg-blue-50
            hover:text-blue-700
            hover:shadow-sm
            active:scale-95
          "
        >
          {item.label}
        </button>
      ))}
    </div>
  </div>
);


  // ── Render ──────────────────────────────────────────────────────────────────
  return (
   
      <div className="orb-theme">
        <Stack>
          <Panel title="ORB Entry">
            {canAccessEntryForm && (
              <ORBEntryForm
                formData={formData}
                handleChange={handleChange}
                handleSubmit={handleSubmit}
                setFormData={setFormData}
                codes={codes}
                availableTanks={availableTanks}
                formatToDateTimeLocal={formatToDateTimeLocal}
                yesterdayDate={yesterdayDate}
                errors={errors}
                canAccessSelectCode={canAccessSelectCode}
              />
            )}

            {canAccessTable && (
              <ORBTable
                entries={chiefPending}
                permissions={{
                  edit: canAccessTableEdit,
                  delete: canAccessTableDelete,
                  // approve: canAccessApprove,
                  // reject: canAccessReject,
                }}
                handlers={{
                  onEdit: handleEdit,
                  onDelete: handleDelete,
                  // onApprove: doApprove,
                  // onReject: doReject,
                }}
              />
            )}
          </Panel>
        </Stack>

        {canAccessReportFilter && (
          <ReportFilter
            onFilterSelect={handleReportPeriod}
            isVisible={isReportVisible}
            onClose={closeReport}
            canAccessFilterReports={canAccessFilterReports}
          />
        )}

        {canAccessReportView && (
          <ReportView
            isVisible={isReportVisible}
            selectedPeriod={selectedPeriod}
            reportData={reportData}
          />
        )}

        {canAccessPendingEntries && (
          <PendingEntriesCard
            pending={chiefPending}
            onApprove={doApprove}
            onReject={doReject}
            canApprove={canAccessApprove}
            canReject={canAccessReject}
          />
        )}

        {canAccessApprovedEntries && (
          <ApprovedEntriesCard
            approved={chiefApproved}
            vessel={vessel}
            onSavePDF={handleSavePDF}
            canAccessSavePDF={canAccessSavePDF}
          />
        )}
      </div>
   
  );
}
