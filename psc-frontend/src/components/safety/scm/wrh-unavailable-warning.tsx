interface SafetyWrhUnavailableWarningProps {
  message: string;
}

export default function SafetyWrhUnavailableWarning({
  message,
}: SafetyWrhUnavailableWarningProps) {
  return (
    <div className="rounded-3xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-800">
      {message}
    </div>
  );
}
