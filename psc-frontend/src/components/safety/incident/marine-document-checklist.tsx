import { useEffect, useState } from "react";

import { SafetyCargoSpecificOverlay } from "./cargo-specific-overlay";

interface SafetyMarineDocumentChecklistProps {
  checklistComplete?: boolean;
  cargoOverlayItems?: Array<{ code: string; status: string }>;
  disabled?: boolean;
  onSaveOther?: (enabled: boolean, text: string) => Promise<void>;
  otherEnabled?: boolean;
  otherText?: string;
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
  disabled = false,
  onSaveOther,
  otherEnabled = false,
  otherText = "",
}: SafetyMarineDocumentChecklistProps) {
  const [isOtherChecked, setIsOtherChecked] = useState(otherEnabled);
  const [otherValue, setOtherValue] = useState(otherText);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setIsOtherChecked(otherEnabled);
    setOtherValue(otherText);
  }, [otherEnabled, otherText]);

  async function saveOtherDocument() {
    if (!onSaveOther) {
      return;
    }
    const cleanedText = otherValue.trim();
    if (isOtherChecked && !cleanedText) {
      setError("Write the other document name.");
      return;
    }
    setError(null);
    setIsSaving(true);
    try {
      await onSaveOther(isOtherChecked, isOtherChecked ? cleanedText : "");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save other document.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5">
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
        <label className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <input
            checked={isOtherChecked}
            disabled={disabled}
            onChange={(event) => setIsOtherChecked(event.target.checked)}
            type="checkbox"
          />
          <span>Other</span>
        </label>
      </div>
      {isOtherChecked ? (
        <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <label className="block text-sm font-medium text-slate-700">
            Specify other document
            <textarea
              className="mt-2 min-h-20 w-full rounded-2xl border border-slate-300 bg-white p-3 text-sm text-slate-900 outline-none focus:border-slate-500"
              disabled={disabled}
              onChange={(event) => setOtherValue(event.target.value)}
              value={otherValue}
            />
          </label>
        </div>
      ) : null}
      {onSaveOther ? (
        <div className="flex flex-wrap items-center gap-3">
          <button
            className="inline-flex min-h-10 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={disabled || isSaving}
            onClick={() => void saveOtherDocument()}
            type="button"
          >
            {isSaving ? "Saving..." : "Save document list"}
          </button>
          {error ? <span className="text-sm font-medium text-rose-700">{error}</span> : null}
        </div>
      ) : null}
      <SafetyCargoSpecificOverlay items={cargoOverlayItems} />
    </section>
  );
}

export default SafetyMarineDocumentChecklist;
