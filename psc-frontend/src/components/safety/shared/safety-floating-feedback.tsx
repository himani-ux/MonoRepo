import type { ReactNode } from "react";

type SafetyFeedbackTone = "error" | "success" | "warning";

interface SafetyFloatingFeedbackProps {
  children: ReactNode;
  tone: SafetyFeedbackTone;
}

const toneClassName: Record<SafetyFeedbackTone, string> = {
  error: "border-rose-200 bg-rose-50 text-rose-900",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
};

export default function SafetyFloatingFeedback({
  children,
  tone,
}: SafetyFloatingFeedbackProps) {
  return (
    <section
      className={`fixed bottom-6 right-6 z-50 min-h-20 w-[min(460px,calc(100vw-3rem))] rounded-2xl border px-6 py-5 text-base font-semibold leading-6 shadow-xl ${toneClassName[tone]}`}
      role={tone === "error" ? "alert" : "status"}
    >
      {children}
    </section>
  );
}
