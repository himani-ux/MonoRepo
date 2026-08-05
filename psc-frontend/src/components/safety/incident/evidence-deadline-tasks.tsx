import type { SafetyEvidenceDeadlineTask } from "../../../schemas/safety/incident-phase3";
import { useState } from "react";

interface SafetyEvidenceDeadlineTasksProps {
  disabled?: boolean;
  onComplete?: (task: SafetyEvidenceDeadlineTask, justification: string) => Promise<void>;
  tasks: SafetyEvidenceDeadlineTask[];
}

const severityTone: Record<SafetyEvidenceDeadlineTask["severity"], string> = {
  ALERT: "border-amber-200 bg-amber-50 text-amber-900",
  HARD_ALARM: "border-rose-200 bg-rose-50 text-rose-900",
  INFO: "border-slate-200 bg-slate-50 text-slate-800",
};

export function SafetyEvidenceDeadlineTasks({
  disabled = false,
  onComplete,
  tasks,
}: SafetyEvidenceDeadlineTasksProps) {
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [savingTask, setSavingTask] = useState<string | null>(null);

  async function completeTask(task: SafetyEvidenceDeadlineTask) {
    if (!onComplete || !task.id) {
      return;
    }
    setSavingTask(task.task_code);
    try {
      await onComplete(task, notes[task.task_code] ?? "");
    } finally {
      setSavingTask(null);
    }
  }

  return (
    <div className="grid gap-3">
        {tasks.length > 0 ? (
          tasks.map((task) => (
            <article
              key={task.task_code}
              className={`rounded-2xl border px-4 py-3 text-sm ${severityTone[task.severity]}`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium">{task.title}</span>
                <span className="text-xs uppercase tracking-[0.18em]">
                  {task.status}
                </span>
              </div>
              {task.justification ? (
                <p className="mt-2 text-xs opacity-80">Note: {task.justification}</p>
              ) : null}
              {onComplete && task.status !== "COMPLETED" ? (
                <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto]">
                  <input
                    className="min-h-10 rounded-xl border border-current/20 bg-white/70 px-3 text-sm text-slate-900 outline-none"
                    disabled={disabled || savingTask === task.task_code}
                    onChange={(event) =>
                      setNotes((current) => ({ ...current, [task.task_code]: event.target.value }))
                    }
                    placeholder="What was done, or why not needed"
                    value={notes[task.task_code] ?? ""}
                  />
                  <button
                    className="min-h-10 rounded-full bg-slate-900 px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
                    disabled={disabled || savingTask === task.task_code}
                    onClick={() => void completeTask(task)}
                    type="button"
                  >
                    {savingTask === task.task_code ? "Saving..." : "Mark done"}
                  </button>
                </div>
              ) : null}
            </article>
          ))
        ) : (
          <p className="text-sm text-slate-500">No urgent evidence tasks yet.</p>
        )}
    </div>
  );
}

export default SafetyEvidenceDeadlineTasks;
