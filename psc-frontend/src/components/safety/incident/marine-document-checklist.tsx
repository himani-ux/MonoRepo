import { SafetyCargoSpecificOverlay } from "./cargo-specific-overlay";

interface SafetyMarineDocumentChecklistProps {
  checklistComplete?: boolean;
  cargoOverlayItems?: Array<{ code: string; status: string }>;
}

const defaultDocuments = [
  "Deck Log",
  "Engine Log",
  "Radio Log",
  "ECDIS track",
  "AIS request",
  "VDR data",
  "Noon / bunker records",
  "ISM / class certs",
];

export function SafetyMarineDocumentChecklist({
  checklistComplete = false,
  cargoOverlayItems = [],
}: SafetyMarineDocumentChecklistProps) {
  return (
    <section className="space-y-5 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Supporting documents
          </p>
          <h2 className="text-xl font-semibold text-slate-900">
            Marine Document Inventory
          </h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {checklistComplete ? "Checklist complete" : "Checklist in progress"}
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {defaultDocuments.map((document) => (
          <label
            key={document}
            className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-700"
          >
            <input checked={checklistComplete} readOnly type="checkbox" />
            <span>{document}</span>
          </label>
        ))}
      </div>
      <SafetyCargoSpecificOverlay items={cargoOverlayItems} />
    </section>
  );
}

export default SafetyMarineDocumentChecklist;
