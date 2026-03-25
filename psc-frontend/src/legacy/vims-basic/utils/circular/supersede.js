const SEQ_DEPARTMENT_IDS = [
  "8949308c-aa8a-ee11-987c-7413ea3d6a70",
];

const TECHNICAL_DEPARTMENT_IDS = [
  "8a49308c-aa8a-ee11-987c-7413ea3d6a70",
];

const normalizeCircularValue = (value) => String(value ?? "").trim();
const normalizeCircularLookupKey = (value) =>
  normalizeCircularValue(value)
    .toLowerCase()
    .replace(/[\s_-]+/g, "");

const getCircularMatchingEntry = (storedValue, nameToIdMap = {}) => {
  const normalizedLookupValue = normalizeCircularLookupKey(storedValue);
  if (!normalizedLookupValue) {
    return null;
  }

  return (
    Object.entries(nameToIdMap).find(
      ([name, id]) =>
        normalizeCircularLookupKey(name) === normalizedLookupValue ||
        normalizeCircularLookupKey(id) === normalizedLookupValue,
    ) || null
  );
};

export const resolveCircularDepartmentUiKey = (storedDept, deptToIdMap = {}) => {
  if (!storedDept) {
    return null;
  }

  const normalizedDept = String(storedDept).trim().toLowerCase();
  const seqIds = [deptToIdMap.Deck, deptToIdMap.SEQ, ...SEQ_DEPARTMENT_IDS]
    .filter(Boolean)
    .map((value) => String(value).trim().toLowerCase());
  const technicalIds = [
    deptToIdMap.Engine,
    deptToIdMap.Technical,
    ...TECHNICAL_DEPARTMENT_IDS,
  ]
    .filter(Boolean)
    .map((value) => String(value).trim().toLowerCase());

  if (
    normalizedDept === "deck" ||
    normalizedDept === "seq" ||
    seqIds.includes(normalizedDept)
  ) {
    return "seq";
  }

  if (
    normalizedDept === "engine" ||
    normalizedDept === "technical" ||
    technicalIds.includes(normalizedDept)
  ) {
    return "technical";
  }

  return null;
};

export const resolveCircularMappedId = (storedValue, nameToIdMap = {}) => {
  const matchingEntry = getCircularMatchingEntry(storedValue, nameToIdMap);
  return matchingEntry ? matchingEntry[1] : null;
};

export const resolveCircularMappedName = (storedValue, nameToIdMap = {}) => {
  const normalizedValue = normalizeCircularValue(storedValue);
  if (!normalizedValue) {
    return null;
  }

  const matchingEntry = getCircularMatchingEntry(storedValue, nameToIdMap);
  return matchingEntry ? matchingEntry[0] : normalizedValue;
};

export const parseCircularStoredArray = (storedValues) => {
  if (!storedValues) {
    return [];
  }

  if (Array.isArray(storedValues)) {
    return storedValues
      .map((storedValue) => normalizeCircularValue(storedValue))
      .filter(Boolean);
  }

  const normalizedValue = normalizeCircularValue(storedValues);
  if (!normalizedValue) {
    return [];
  }

  try {
    const parsedValue = JSON.parse(normalizedValue);
    if (Array.isArray(parsedValue)) {
      return parsedValue
        .map((storedValue) => normalizeCircularValue(storedValue))
        .filter(Boolean);
    }
  } catch (error) {
    // Fall back to comma-separated parsing when the stored value is plain text.
  }

  return normalizedValue
    .split(",")
    .map((storedValue) => normalizeCircularValue(storedValue))
    .filter(Boolean);
};

export const resolveCircularMappedIds = (storedValues, nameToIdMap = {}) =>
  parseCircularStoredArray(storedValues)
    .map((storedValue) => resolveCircularMappedId(storedValue, nameToIdMap))
    .filter(Boolean);

export const resolveCircularMappedNames = (storedValues, nameToIdMap = {}) =>
  parseCircularStoredArray(storedValues)
    .map((storedValue) => resolveCircularMappedName(storedValue, nameToIdMap))
    .filter(Boolean);
