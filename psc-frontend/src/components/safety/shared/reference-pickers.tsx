import { useEffect, useMemo, useState } from "react";

import {
  safetyApi,
  type SafetyReferenceIncidentTypeOption,
  type SafetyReferenceLossTypeOption,
  type SafetyReferenceMscatOption,
  type SafetyReferenceSoiItemOption,
} from "../../../lib/api/safety";

type PickerStatus = "idle" | "loading" | "ready" | "error";

function useReferenceOptions<T>(loader: () => Promise<T[]>, deps: unknown[] = []) {
  const [options, setOptions] = useState<T[]>([]);
  const [status, setStatus] = useState<PickerStatus>("idle");

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    Promise.resolve()
      .then(loader)
      .then((nextOptions) => {
        if (!cancelled) {
          setOptions(Array.isArray(nextOptions) ? nextOptions : []);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setOptions([]);
          setStatus("error");
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { options, status };
}

function selectClassName(className?: string) {
  return className ?? "min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2";
}

export function SafetyIncidentTypeSelect({
  className,
  label = "Incident type",
  onChange,
  value,
}: {
  className?: string;
  label?: string;
  onChange: (value: number | null) => void;
  value?: number | null;
}) {
  const { options, status } = useReferenceOptions<SafetyReferenceIncidentTypeOption>(
    () => safetyApi.getReferenceIncidentTypes(),
    [],
  );
  const activeOptions = options.filter((option) => option.active);

  return (
    <select
      aria-label={label}
      className={selectClassName(className)}
      onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)}
      value={value ?? ""}
    >
      <option value="">
        {status === "loading" ? "Loading incident types..." : "Select incident type"}
      </option>
      {activeOptions.map((option) => (
        <option key={option.id} value={option.legacy_int_id}>
          {option.type_code} - {option.type_name}
        </option>
      ))}
    </select>
  );
}

export function SafetyLossTypeSelect({
  className,
  label = "Type of loss",
  onChange,
  value,
}: {
  className?: string;
  label?: string;
  onChange: (value: number | null) => void;
  value?: number | null;
}) {
  const { options, status } = useReferenceOptions<SafetyReferenceLossTypeOption>(
    () => safetyApi.getReferenceLossTypes(),
    [],
  );
  const activeOptions = options.filter((option) => option.active);

  return (
    <select
      aria-label={label}
      className={selectClassName(className)}
      onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)}
      value={value ?? ""}
    >
      <option value="">
        {status === "loading" ? "Loading loss types..." : "Select loss type"}
      </option>
      {activeOptions.map((option) => (
        <option key={option.id} value={option.loss_type_id}>
          {option.loss_type_name}
        </option>
      ))}
    </select>
  );
}

export function SafetyMscatPicker({
  className,
  label = "M-SCAT code",
  onChange,
  value,
}: {
  className?: string;
  label?: string;
  onChange: (value: { categoryId: number | null; subcodeId: string | null }) => void;
  value?: { categoryId?: number | null; subcodeId?: string | null };
}) {
  const [query, setQuery] = useState("");
  const { options, status } = useReferenceOptions<SafetyReferenceMscatOption>(
    () => safetyApi.getReferenceMscat(),
    [],
  );
  const selectedValue = value?.subcodeId ?? "";
  const filteredOptions = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return options
      .filter((option) => option.active)
      .filter((option) => {
        if (!normalizedQuery) {
          return true;
        }
        return [
          String(option.category_id),
          option.category_name,
          option.subcode_id,
          option.subcode_description,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);
      })
      .slice(0, 80);
  }, [options, query]);

  return (
    <div className="space-y-2">
      <input
        aria-label={`${label} search`}
        className={selectClassName(className)}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search by prefix, category, or description"
        value={query}
      />
      <select
        aria-label={label}
        className={selectClassName(className)}
        onChange={(event) => {
          const selected = options.find((option) => option.subcode_id === event.target.value);
          onChange({
            categoryId: selected?.category_id ?? null,
            subcodeId: selected?.subcode_id ?? null,
          });
        }}
        value={selectedValue}
      >
        <option value="">{status === "loading" ? "Loading M-SCAT..." : "Select M-SCAT code"}</option>
        {filteredOptions.map((option) => (
          <option key={option.id} value={option.subcode_id}>
            {option.category_id} {option.category_name} / {option.subcode_id} - {option.subcode_description}
          </option>
        ))}
      </select>
    </div>
  );
}

export function SafetySoiItemSelect({
  areaId,
  className,
  onChange,
  value,
}: {
  areaId?: number | null;
  className?: string;
  onChange: (value: number | null) => void;
  value?: number | null;
}) {
  const { options, status } = useReferenceOptions<SafetyReferenceSoiItemOption>(
    () => safetyApi.getReferenceSoiItems(areaId),
    [areaId],
  );
  const activeOptions = options.filter((option) => option.active);

  return (
    <select
      aria-label="SOI item"
      className={selectClassName(className)}
      disabled={!areaId}
      onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)}
      value={value ?? ""}
    >
      <option value="">
        {status === "loading" ? "Loading SOI items..." : "Select checklist item"}
      </option>
      {activeOptions.map((option) => (
        <option key={option.id} value={option.legacy_int_id}>
          {option.subsection_id} {option.item_number} - {option.description}
        </option>
      ))}
    </select>
  );
}
