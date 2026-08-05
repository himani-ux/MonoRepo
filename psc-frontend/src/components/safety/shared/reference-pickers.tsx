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

function isRemovedIncidentType(option: SafetyReferenceIncidentTypeOption) {
  return (
    option.type_code === "IMO_MISSING_VESSEL" ||
    option.type_name.trim().toLowerCase() === "missing vessel"
  );
}

export function SafetyIncidentTypeSelect({
  className,
  label = "What type of incident?",
  onChange,
  onSelectedOptionChange,
  value,
}: {
  className?: string;
  label?: string;
  onChange: (value: number | null) => void;
  onSelectedOptionChange?: (option: SafetyReferenceIncidentTypeOption | null) => void;
  value?: number | null;
}) {
  const { options, status } = useReferenceOptions<SafetyReferenceIncidentTypeOption>(
    () => safetyApi.getReferenceIncidentTypes(),
    [],
  );
  const activeOptions = options.filter((option) => option.active && !isRemovedIncidentType(option));
  const selectedOption = activeOptions.find((option) => option.legacy_int_id === value) ?? null;

  useEffect(() => {
    onSelectedOptionChange?.(selectedOption);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedOption?.legacy_int_id]);

  return (
    <select
      aria-label={label}
      className={selectClassName(className)}
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
        {status === "loading" ? "Loading incident types..." : "Select incident type"}
      </option>
      {activeOptions.map((option) => (
        <option key={option.id} value={option.legacy_int_id}>
          {option.type_name}
        </option>
      ))}
    </select>
  );
}

export function SafetyLossTypeSelect({
  className,
  label = "What was affected?",
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
        {status === "loading" ? "Loading options..." : "Select what was affected"}
      </option>
      {activeOptions.map((option) => (
        <option key={option.id} value={option.loss_type_id}>
          {option.loss_type_name}
        </option>
      ))}
    </select>
  );
}

export function SafetyLossTypeMultiSelect({
  className,
  label = "What was affected?",
  maxSelections = 3,
  onChange,
  otherText,
  values,
}: {
  className?: string;
  label?: string;
  maxSelections?: number;
  onChange: (value: {
    lossTypeIds: number[];
    otherSelected: boolean;
    otherText: string;
  }) => void;
  otherText?: string | null;
  values: {
    lossTypeIds: number[];
    otherSelected: boolean;
  };
}) {
  const { options, status } = useReferenceOptions<SafetyReferenceLossTypeOption>(
    () => safetyApi.getReferenceLossTypes(),
    [],
  );
  const [isOpen, setIsOpen] = useState(false);
  const activeOptions = options.filter((option) => option.active);
  const selectedIds = values.lossTypeIds.filter((value) => Number.isFinite(value));
  const selectedCount = selectedIds.length + (values.otherSelected ? 1 : 0);
  const selectedLabels = activeOptions
    .filter((option) => selectedIds.includes(option.loss_type_id))
    .map((option) => option.loss_type_name);
  if (values.otherSelected) {
    selectedLabels.push(otherText?.trim() ? `Other: ${otherText.trim()}` : "Other - write details");
  }
  const displayValue = selectedLabels.length
    ? selectedLabels.join(", ")
    : status === "loading"
      ? "Loading options..."
      : "Select what was affected";

  function updateLossType(lossTypeId: number, checked: boolean) {
    const nextIds = checked
      ? [...selectedIds, lossTypeId]
      : selectedIds.filter((value) => value !== lossTypeId);
    onChange({
      lossTypeIds: nextIds.slice(0, maxSelections),
      otherSelected: values.otherSelected,
      otherText: otherText ?? "",
    });
  }

  function updateOther(checked: boolean) {
    onChange({
      lossTypeIds: selectedIds,
      otherSelected: checked,
      otherText: checked ? otherText ?? "" : "",
    });
  }

  return (
    <div className={className ?? "space-y-3"}>
      <div className="relative">
        <button
          aria-expanded={isOpen}
          aria-label={label}
          className={`${selectClassName()} flex items-center justify-between gap-3 bg-white text-left`}
          onBlur={() => {
            window.setTimeout(() => setIsOpen(false), 120);
          }}
          onClick={() => setIsOpen((current) => !current)}
          type="button"
        >
          <span className={selectedLabels.length ? "truncate text-slate-900" : "text-slate-500"}>
            {displayValue}
          </span>
          <span className="shrink-0 text-xs text-slate-500">{selectedCount}/{maxSelections}</span>
        </button>
        {isOpen ? (
          <div className="absolute z-30 mt-2 max-h-72 w-full overflow-y-auto rounded-2xl border border-slate-200 bg-white p-1 shadow-lg">
            {status === "loading" ? (
              <p className="px-3 py-2 text-sm text-slate-500">Loading options...</p>
            ) : null}
            {activeOptions.map((option) => {
              const checked = selectedIds.includes(option.loss_type_id);
              const disabled = !checked && selectedCount >= maxSelections;
              return (
                <label
                  className={`flex cursor-pointer items-start gap-3 rounded-xl px-3 py-2 text-sm hover:bg-slate-50 ${
                    checked ? "bg-slate-100 font-medium text-slate-900" : "text-slate-700"
                  } ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
                  key={option.id}
                  onMouseDown={(event) => event.preventDefault()}
                >
                  <input
                    checked={checked}
                    className="mt-1 h-4 w-4 rounded border-slate-300"
                    disabled={disabled}
                    onChange={(event) => updateLossType(option.loss_type_id, event.target.checked)}
                    type="checkbox"
                  />
                  <span className="leading-5">{option.loss_type_name}</span>
                </label>
              );
            })}
            <label
              className={`flex cursor-pointer items-start gap-3 rounded-xl px-3 py-2 text-sm hover:bg-slate-50 ${
                values.otherSelected ? "bg-slate-100 font-medium text-slate-900" : "text-slate-700"
              } ${!values.otherSelected && selectedCount >= maxSelections ? "cursor-not-allowed opacity-50" : ""}`}
              onMouseDown={(event) => event.preventDefault()}
            >
              <input
                checked={values.otherSelected}
                className="mt-1 h-4 w-4 rounded border-slate-300"
                disabled={!values.otherSelected && selectedCount >= maxSelections}
                onChange={(event) => updateOther(event.target.checked)}
                type="checkbox"
              />
              <span className="leading-5">Other - write details</span>
            </label>
          </div>
        ) : null}
      </div>
      {values.otherSelected ? (
        <input
          aria-label={`${label} other details`}
          className={selectClassName()}
          maxLength={256}
          onChange={(event) =>
            onChange({
              lossTypeIds: selectedIds,
              otherSelected: true,
              otherText: event.target.value,
            })
          }
          placeholder="Write what was affected"
          value={otherText ?? ""}
        />
      ) : null}
    </div>
  );
}

export function SafetyMscatPicker({
  className,
  label = "Cause code",
  bottomOptionLabel,
  onBottomOptionSelect,
  onChange,
  value,
}: {
  className?: string;
  label?: string;
  bottomOptionLabel?: string;
  onBottomOptionSelect?: () => void;
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
      .sort((left, right) => {
        if (left.category_id !== right.category_id) {
          return left.category_id - right.category_id;
        }
        return compareNaturalItemNumber(left.subcode_id, right.subcode_id);
      });
  }, [options, query]);
  const groupedFilteredOptions = useMemo(() => {
    const groups: Array<{
      categoryId: number;
      categoryName: string;
      options: SafetyReferenceMscatOption[];
    }> = [];
    const groupIndex = new Map<string, number>();

    filteredOptions.forEach((option) => {
      const key = `${option.category_id}-${option.category_name}`;
      let index = groupIndex.get(key);
      if (index === undefined) {
        index = groups.length;
        groupIndex.set(key, index);
        groups.push({
          categoryId: option.category_id,
          categoryName: option.category_name,
          options: [],
        });
      }
      groups[index].options.push(option);
    });

    return groups;
  }, [filteredOptions]);

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
            groupedFilteredOptions.map((group) => (
              <div key={`${group.categoryId}-${group.categoryName}`}>
                <div className="sticky top-0 z-10 rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-semibold uppercase text-slate-600">
                  {group.categoryId} {group.categoryName}
                </div>
                {group.options.map((option) => (
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
                  </button>
                ))}
              </div>
            ))
          ) : (
            <div className="px-3 py-2 text-sm text-slate-500">No matching cause code found.</div>
          )}
          {bottomOptionLabel ? (
            <button
              className="mt-1 block w-full rounded-xl border-t border-slate-100 px-3 py-2 text-left text-sm font-medium text-slate-800 hover:bg-slate-50 focus:bg-slate-50 focus:outline-none"
              onMouseDown={(event) => {
                event.preventDefault();
                setQuery(bottomOptionLabel);
                setIsOpen(false);
                onBottomOptionSelect?.();
              }}
              type="button"
            >
              {bottomOptionLabel}
            </button>
          ) : null}
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
