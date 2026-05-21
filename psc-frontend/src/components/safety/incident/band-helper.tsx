interface SafetyBandHelperProps {
  advisoryBand?: "GREEN" | "YELLOW" | "RED";
}

const bandCopy = {
  GREEN: {
    accent: "border-emerald-200 bg-emerald-50 text-emerald-800",
    body: "GREEN keeps the closer path with PIC and the lightest investigation footprint.",
    title: "GREEN advisory",
  },
  RED: {
    accent: "border-rose-200 bg-rose-50 text-rose-800",
    body: "RED triggers FM and Managing Director notification plus the external-expert engagement prompt.",
    title: "RED advisory",
  },
  YELLOW: {
    accent: "border-amber-200 bg-amber-50 text-amber-800",
    body: "YELLOW routes closure authority to DPA and keeps the incident in the joint-investigation lane.",
    title: "YELLOW advisory",
  },
} as const;

export function SafetyBandHelper({
  advisoryBand = "GREEN",
}: SafetyBandHelperProps) {
  const copy = bandCopy[advisoryBand];

  return (
    <section className={`rounded-3xl border p-5 shadow-sm ${copy.accent}`}>
      <h2 className="text-lg font-semibold">{copy.title}</h2>
      <p className="mt-2 text-sm leading-6">{copy.body}</p>
    </section>
  );
}

export default SafetyBandHelper;
