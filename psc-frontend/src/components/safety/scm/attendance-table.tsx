export interface SafetyScmAttendanceRow {
  crewId: string;
  displayName: string;
  rankName: string;
  present: boolean;
  signature?: {
    required: boolean;
    signedAt: string | null;
    signerRole: "CO" | "ATTENDEE" | "MASTER";
    status: "SIGNED" | "NOT_SIGNED" | "NOT_REQUIRED";
    typedName: string | null;
  };
  wrhFlag: "GREEN" | "YELLOW" | "RED";
  wrhRest24h: string;
  wrhRest7d: string;
}

interface SafetyAttendanceTableProps {
  isSigning?: boolean;
  onCaptureSignature?: (row: SafetyScmAttendanceRow) => void;
  rows: SafetyScmAttendanceRow[];
}

const flagClasses: Record<SafetyScmAttendanceRow["wrhFlag"], string> = {
  GREEN: "bg-emerald-50 text-emerald-700",
  YELLOW: "bg-amber-50 text-amber-700",
  RED: "bg-rose-50 text-rose-700",
};

export default function SafetyAttendanceTable({
  isSigning = false,
  onCaptureSignature,
  rows,
}: SafetyAttendanceTableProps) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-slate-600">
          <tr>
            <th className="px-4 py-3 font-medium">Crew</th>
            <th className="px-4 py-3 font-medium">Rank</th>
            <th className="px-4 py-3 font-medium">Present</th>
            <th className="px-4 py-3 font-medium">WRH flag</th>
            <th className="px-4 py-3 font-medium">Rest 24h</th>
            <th className="px-4 py-3 font-medium">Rest 7d</th>
            <th className="px-4 py-3 font-medium">Signature</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row) => (
            <tr key={row.crewId}>
              <td className="px-4 py-4 text-slate-900">{row.displayName}</td>
              <td className="px-4 py-4 text-slate-600">{row.rankName}</td>
              <td className="px-4 py-4 text-slate-600">{row.present ? "Present" : "Absent"}</td>
              <td className="px-4 py-4">
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${flagClasses[row.wrhFlag]}`}>
                  {row.wrhFlag}
                </span>
              </td>
              <td className="px-4 py-4 text-slate-600">{row.wrhRest24h}</td>
              <td className="px-4 py-4 text-slate-600">{row.wrhRest7d}</td>
              <td className="px-4 py-4">
                <SignatureCell
                  isSigning={isSigning}
                  onCaptureSignature={onCaptureSignature}
                  row={row}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SignatureCell({
  isSigning,
  onCaptureSignature,
  row,
}: {
  isSigning: boolean;
  onCaptureSignature?: (row: SafetyScmAttendanceRow) => void;
  row: SafetyScmAttendanceRow;
}) {
  const signature = row.signature;
  if (!row.present) {
    return <span className="text-xs text-slate-500">Not required</span>;
  }
  if (signature?.status === "SIGNED") {
    return (
      <div className="space-y-1">
        <span className="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          Signed
        </span>
        <div className="text-xs text-slate-500">
          {signature.typedName ?? row.displayName}
          {signature.signedAt ? ` / ${signature.signedAt}` : ""}
        </div>
      </div>
    );
  }
  return (
    <button
      className="min-h-[36px] rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
      disabled={isSigning || !onCaptureSignature}
      onClick={() => onCaptureSignature?.(row)}
      type="button"
    >
      {isSigning ? "Signing..." : "Capture signature"}
    </button>
  );
}
