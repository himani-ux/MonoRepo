import type { SafetyPhase8DeadlinePause } from "../../../schemas/safety/incident-phase8";

interface SafetyDeadlinePauseBannerProps {
  status: SafetyPhase8DeadlinePause;
}

export default function SafetyDeadlinePauseBanner({
  status,
}: SafetyDeadlinePauseBannerProps) {
  if (!status.is_paused) {
    return null;
  }

  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
      <p className="font-semibold">YELLOW-band deadline paused</p>
      <p className="mt-1">
        The DPA leave flag is active, so the closure clock is paused in this handover workspace.
      </p>
    </div>
  );
}
