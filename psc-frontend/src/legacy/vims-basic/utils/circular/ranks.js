const CIRCULAR_DECK_RANK_NAMES = [
  "Master",
  "Acting Master",
  "Chief Officer",
  "Second Officer",
  "Third Officer",
  "Deck Fitter",
  "Deck Cadet",
  "Bosun",
  "Able Bodied Seaman",
  "Ordinary Seaman",
  "Cook",
  "Messman",
  "Welder",
];

const normalizeRankName = (value) =>
  String(value ?? "")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase();

const compactRankName = (value) => normalizeRankName(value).replace(/[\s_-]+/g, "");

const CIRCULAR_DECK_RANK_NAME_LOOKUP = new Set(
  CIRCULAR_DECK_RANK_NAMES.map(normalizeRankName),
);

export const getCircularRankDisplayName = (rank) =>
  String(rank?.rank_name ?? rank?.name ?? rank?.rank_id ?? "").trim();

export const isDisplayableCircularRank = (rank) => {
  const displayName = getCircularRankDisplayName(rank);
  return Boolean(displayName) && compactRankName(displayName) !== "notselected";
};

export const isCircularDeckRank = (rank) =>
  CIRCULAR_DECK_RANK_NAME_LOOKUP.has(
    normalizeRankName(getCircularRankDisplayName(rank)),
  );

export const getDisplayableCircularRanks = (ranks) =>
  Array.isArray(ranks) ? ranks.filter(isDisplayableCircularRank) : [];

export const splitCircularRanksByDepartment = (ranks) => {
  const displayableRanks = getDisplayableCircularRanks(ranks);

  return {
    deckRanks: displayableRanks.filter(isCircularDeckRank),
    technicalRanks: displayableRanks.filter((rank) => !isCircularDeckRank(rank)),
  };
};
