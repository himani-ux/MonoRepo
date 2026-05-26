import { useEffect, useMemo, useState } from "react";

import {
  safetyApi,
  type SafetyReferenceIncidentTypeOption,
  type SafetyReferenceLossTypeOption,
  type SafetyReferenceMscatOption,
  type SafetyReferenceSoiItemOption,
} from "../../../lib/api/safety";

type PickerStatus = "idle" | "loading" | "ready" | "error";

function naturalNumberParts(value: string | number | null | undefined) {
  return Array.from(String(value ?? "").matchAll(/\d+/g), (match) => Number(match[0]));
}

function compareNaturalItemNumber(left: string, right: string) {
  const leftParts = naturalNumberParts(left);
  const rightParts = naturalNumberParts(right);
  const maxLength = Math.max(leftParts.length, rightParts.length);
  for (let index = 0; index < maxLength; index += 1) {
    const leftValue = leftParts[index] ?? -1;
    const rightValue = rightParts[index] ?? -1;
    if (leftValue !== rightValue) {
      return leftValue - rightValue;
    }
  }
  return left.localeCompare(right);
}

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
  const [isOpen, setIsOpen] = useState(false);
  const { options, status } = useReferenceOptions<SafetyReferenceMscatOption>(
    () => safetyApi.getReferenceMscat(),
    [],
  );
  const selectedValue = value?.subcodeId ?? "";
  const selectedOption = useMemo(
    () => options.find((option) => option.subcode_id === selectedValue),
    [options, selectedValue],
  );
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

  useEffect(() => {
    if (!selectedOption) {
      return;
    }
    setQuery(`${selectedOption.subcode_id} - ${selectedOption.subcode_description}`);
  }, [selectedOption]);

  return (
    <div className="relative">
      <input
        aria-expanded={isOpen}
        aria-label={`${label} search`}
        autoComplete="off"
        className={selectClassName(className)}
        onBlur={() => {
          window.setTimeout(() => setIsOpen(false), 120);
        }}
        onChange={(event) => {
          const nextValue = event.target.value;
          setQuery(nextValue);
          setIsOpen(true);
          onChange({ categoryId: null, subcodeId: null });
        }}
        onFocus={() => setIsOpen(true)}
        placeholder={status === "loading" ? `Loading ${label}...` : `Search ${label}`}
        value={query}
      />
      {isOpen && (
        <div className="absolute z-30 mt-2 max-h-72 w-full overflow-y-auto rounded-2xl border border-slate-200 bg-white p-1 shadow-lg">
          {filteredOptions.length ? (
            filteredOptions.map((option) => (
              <button
                className="block w-full rounded-xl px-3 py-2 text-left text-sm text-slate-800 hover:bg-slate-50 focus:bg-slate-50 focus:outline-none"
                key={option.id}
                onMouseDown={(event) => {
                  event.preventDefault();
                  setQuery(`${option.subcode_id} - ${option.subcode_description}`);
                  setIsOpen(false);
                  onChange({
                    categoryId: option.category_id,
                    subcodeId: option.subcode_id,
                  });
                }}
                type="button"
              >
                <span className="block font-medium text-slate-900">
                  {option.subcode_id} - {option.subcode_description}
                </span>
                <span className="block text-xs text-slate-500">
                  {option.category_id} {option.category_name}
                </span>
              </button>
            ))
          ) : (
            <div className="px-3 py-2 text-sm text-slate-500">No matching root cause found.</div>
          )}
        </div>
      )}
    </div>
  );
}

export function SafetySoiItemSelect({
  areaId,
  className,
  onChange,
  onSelectedOptionChange,
  value,
}: {
  areaId?: number | null;
  className?: string;
  onChange: (value: number | null) => void;
  onSelectedOptionChange?: (option: SafetyReferenceSoiItemOption | null) => void;
  value?: number | null;
}) {
  const { options, status } = useReferenceOptions<SafetyReferenceSoiItemOption>(
    () => safetyApi.getReferenceSoiItems(areaId),
    [areaId],
  );
  const activeOptions = [...options]
    .filter((option) => option.active)
    .sort((left, right) => {
      if (left.area_id !== right.area_id) {
        return left.area_id - right.area_id;
      }
      if (left.subsection_id !== right.subsection_id) {
        return left.subsection_id - right.subsection_id;
      }
      return compareNaturalItemNumber(left.item_number, right.item_number);
    });

  return (
    <select
      aria-label="SOI item"
      className={selectClassName(className)}
      disabled={!areaId}
      onChange={(event) => {
        const nextValue = event.target.value ? Number(event.target.value) : null;
        onChange(nextValue);
        onSelectedOptionChange?.(
          nextValue === null
            ? null
            : activeOptions.find((option) => option.legacy_int_id === nextValue) ?? null,
        );
      }}
      value={value ?? ""}
    >
      <option value="">
        {status === "loading" ? "Loading SOI items..." : "Select checklist item"}
      </option>
      {activeOptions.map((option) => (
        <option key={option.id} value={option.legacy_int_id}>
          {option.item_number} - {option.description}
        </option>
      ))}
    </select>
  );
}
