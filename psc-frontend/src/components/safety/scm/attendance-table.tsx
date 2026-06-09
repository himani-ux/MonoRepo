export interface SafetyScmAttendanceRow {
  crewId: string;
  displayName: string;
  rankName: string;
  present: boolean;
  wrhFlag: "GREEN" | "YELLOW" | "RED";
  wrhRest24h: string;
  wrhRest7d: string;
}

interface SafetyAttendanceTableProps {
  rows: SafetyScmAttendanceRow[];
}

const flagClasses: Record<SafetyScmAttendanceRow["wrhFlag"], string> = {
  GREEN: "bg-emerald-50 text-emerald-700",
  YELLOW: "bg-amber-50 text-amber-700",
  RED: "bg-rose-50 text-rose-700",
};

export default function SafetyAttendanceTable({ rows }: SafetyAttendanceTableProps) {
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
