const DEVICE_FINGERPRINT_STORAGE_KEY = "vims:safety:device-fingerprint";
const MAX_DEVICE_FINGERPRINT_LENGTH = 128;

type SignatureUser = {
  UserName?: string | null;
  crewId?: string | number | null;
  crew_id?: string | number | null;
  displayName?: string | null;
  display_name?: string | null;
  employeeId?: string | number | null;
  employee_id?: string | number | null;
  firstName?: string | null;
  first_name?: string | null;
  fullName?: string | null;
  full_name?: string | null;
  id?: string | number | null;
  login_id?: string | null;
  surname?: string | null;
  userName?: string | null;
  username?: string | null;
};

function firstNonBlank(...values: Array<string | number | null | undefined>) {
  for (const value of values) {
    const text = String(value ?? "").trim();
    if (text) {
      return text;
    }
  }
  return "";
}

function buildBrowserFingerprint() {
  if (typeof window === "undefined") {
    return "server-render";
  }

  const navigatorPart = [
    window.navigator.platform,
    window.navigator.language,
    window.navigator.userAgent.slice(0, 120),
  ]
    .filter(Boolean)
    .join("|");
  const screenPart = `${window.screen?.width ?? 0}x${window.screen?.height ?? 0}x${window.screen?.colorDepth ?? 0}`;
  const timezonePart = Intl.DateTimeFormat().resolvedOptions().timeZone || "timezone-unknown";
  return [navigatorPart, screenPart, timezonePart].filter(Boolean).join("::");
}

function createFingerprint() {
  const randomId =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2);
  return compactFingerprint(`${buildBrowserFingerprint()}::${randomId}`);
}

function fingerprintHash(value: string) {
  let hash = 5381;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 33) ^ value.charCodeAt(index);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function compactFingerprint(value: string) {
  const normalized = value.trim();
  if (normalized.length <= MAX_DEVICE_FINGERPRINT_LENGTH) {
    return normalized;
  }
  return `fp:${fingerprintHash(normalized)}:${normalized.slice(-24)}`;
}

export function getSafetyDeviceFingerprint() {
  if (typeof window === "undefined") {
    return createFingerprint();
  }

  try {
    const existing = window.localStorage.getItem(DEVICE_FINGERPRINT_STORAGE_KEY);
    if (existing?.trim()) {
      const compacted = compactFingerprint(existing);
      if (compacted !== existing) {
        window.localStorage.setItem(DEVICE_FINGERPRINT_STORAGE_KEY, compacted);
      }
      return compacted;
    }
    const next = createFingerprint();
    window.localStorage.setItem(DEVICE_FINGERPRINT_STORAGE_KEY, next);
    return next;
  } catch {
    return createFingerprint();
  }
}

export function resolveSignatureTypedName(user: SignatureUser | null | undefined) {
  const combinedName = [user?.firstName ?? user?.first_name, user?.surname]
    .map((value) => String(value ?? "").trim())
    .filter(Boolean)
    .join(" ");

  return firstNonBlank(
    user?.fullName,
    user?.full_name,
    user?.displayName,
    user?.display_name,
    combinedName,
    user?.username,
    user?.userName,
    user?.UserName,
    user?.login_id,
    user?.crewId,
    user?.crew_id,
    user?.employeeId,
    user?.employee_id,
    user?.id,
  );
}
