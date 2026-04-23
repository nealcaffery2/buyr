"use client";

import { CheckCircle, Loader2 } from "lucide-react";

const STEP_ORDER = [
  "parsing_address",
  "finding_wholesalers",
  "searching_county_records",
  "ranking_buyers",
  "opencorporates_lookup",
  "skip_tracing",
  "complete",
];

export function ProgressStepper({
  currentStep,
  percent,
  stepLabels,
}: {
  currentStep: string;
  percent: number;
  stepLabels: Record<string, string>;
}) {
  const currentIdx = STEP_ORDER.indexOf(currentStep);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-white">
          {stepLabels[currentStep] ?? currentStep}
        </span>
        <span className="text-sm text-slate-400">{percent}%</span>
      </div>

      <div className="w-full bg-slate-800 rounded-full h-1.5">
        <div
          className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>

      <div className="grid grid-cols-2 gap-2 pt-2">
        {STEP_ORDER.filter((s) => s !== "complete").map((step, idx) => {
          const done = idx < currentIdx;
          const active = idx === currentIdx;
          return (
            <div
              key={step}
              className={`flex items-center gap-2 text-xs ${
                done
                  ? "text-green-400"
                  : active
                    ? "text-blue-400"
                    : "text-slate-600"
              }`}
            >
              {done ? (
                <CheckCircle size={12} />
              ) : active ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <div className="w-3 h-3 rounded-full border border-slate-700" />
              )}
              {stepLabels[step]}
            </div>
          );
        })}
      </div>
    </div>
  );
}
