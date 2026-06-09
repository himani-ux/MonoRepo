export function formatScmState(state: string | null | undefined) {
  switch (String(state || "").toUpperCase()) {
    case "DRAFT":
      return "Draft";
    case "SUBMITTED":
      return "Submitted to Office";
    case "SIGNED_OFF":
      return "Signed Off";
    case "REOPENED":
      return "Reopened";
    case "CLOSED":
      return "Closed";
    default:
      return state || "Not recorded";
  }
}
