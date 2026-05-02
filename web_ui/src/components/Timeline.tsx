import { AlertCircle, CheckCircle2, Circle, Loader2 } from "lucide-react";
import clsx from "clsx";
import type { Stage } from "@/lib/api";

export function Timeline({ stages, onRetry }: { stages: Stage[]; onRetry?: () => void }) {
  return (
    <div className="space-y-3">
      {stages.map((stage) => (
        <div key={stage.name} className="grid grid-cols-[28px_1fr] gap-3">
          <div className="pt-1">
            {stage.status === "completed" && <CheckCircle2 className="h-5 w-5 text-emerald-400" />}
            {stage.status === "failed" && <AlertCircle className="h-5 w-5 text-red-400" />}
            {stage.status === "in_progress" && <Loader2 className="h-5 w-5 animate-spin text-signal" />}
            {stage.status === "waiting" && <Circle className="h-5 w-5 text-slate-600" />}
          </div>
          <div className={clsx("rounded-md border border-line bg-panel p-4", stage.status === "in_progress" && "ring-1 ring-signal/60")}>
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold">{stage.name}</h3>
              <span className="text-xs uppercase tracking-wide text-slate-400">{stage.status.replace("_", " ")}</span>
            </div>
            {stage.error && (
              <div className="mt-3 text-sm text-red-200">
                <p>{stage.error}</p>
                {onRetry && (
                  <button onClick={onRetry} className="mt-3 rounded-md bg-red-500 px-3 py-2 text-sm font-medium text-white hover:bg-red-400">
                    Retry
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
