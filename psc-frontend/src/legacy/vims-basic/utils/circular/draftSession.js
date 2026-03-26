const DRAFT_EDIT_SESSION_KEY = "circularDraftEditSession";
const LEGACY_DRAFT_KEYS = [
  "editingDraftData",
  "editingDraftId",
  "editingDraftSrNo",
];

const normalizeDraftSession = (draftData, explicitDraftId, explicitDraftSrNo) => {
  if (!draftData || typeof draftData !== "object") {
    return null;
  }

  const draftId = String(explicitDraftId || draftData.id || "")
    .trim()
    .toLowerCase();
  const draftSrNo = String(explicitDraftSrNo || draftData.sr_no || "").trim();

  if (!draftSrNo) {
    return null;
  }

  return {
    draftId: draftId || null,
    draftSrNo,
    draftData,
  };
};

const readLegacyDraftSession = () => {
  const rawDraftData = localStorage.getItem("editingDraftData");
  if (!rawDraftData) {
    return null;
  }

  try {
    const parsedDraftData = JSON.parse(rawDraftData);
    return normalizeDraftSession(
      parsedDraftData,
      localStorage.getItem("editingDraftId"),
      localStorage.getItem("editingDraftSrNo"),
    );
  } catch (error) {
    console.error("readLegacyDraftSession: failed to parse editingDraftData", error);
    return null;
  }
};

export const clearCircularDraftEditSession = () => {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem(DRAFT_EDIT_SESSION_KEY);
  LEGACY_DRAFT_KEYS.forEach((key) => localStorage.removeItem(key));
};

export const setCircularDraftEditSession = (draftData) => {
  if (typeof window === "undefined") {
    return null;
  }

  const session = normalizeDraftSession(draftData);
  if (!session) {
    return null;
  }

  clearCircularDraftEditSession();
  localStorage.setItem(DRAFT_EDIT_SESSION_KEY, JSON.stringify(session));
  return session;
};

export const getCircularDraftEditSession = () => {
  if (typeof window === "undefined") {
    return null;
  }

  let session = null;
  const rawSession = localStorage.getItem(DRAFT_EDIT_SESSION_KEY);
  if (rawSession) {
    try {
      const parsedSession = JSON.parse(rawSession);
      session = normalizeDraftSession(
        parsedSession?.draftData,
        parsedSession?.draftId,
        parsedSession?.draftSrNo,
      );
    } catch (error) {
      console.error("consumeCircularDraftEditSession: failed to parse session", error);
    }
  }

  if (!session) {
    session = readLegacyDraftSession();
  }

  return session;
};

export const consumeCircularDraftEditSession = () => {
  const session = getCircularDraftEditSession();
  clearCircularDraftEditSession();
  return session;
};
