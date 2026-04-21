"use client";

import { CheckCircle2, Loader2, Circle } from "lucide-react";

const STEPS = [
  { key: "parsing_address",        label: "Parsing address" },
  { key: "finding_wholesalers",    label: "Finding wholesalers" },
  { key: "searching_county_records", label: "Searching county records" },
  { key: "ranking_buyers",         label: "Ranking buyers" },
  { key: "opencorporates_lookup",  label: "Looking up LLCs" },
  { key: "skip_tracing",           label: "Skip tracing contacts" },
  { key: "complete",               label: "Done" },
];

export function PipelineStatus({
  step,
  percent,
}: {
  step: string;
  percent: number;
}) {
  const currentIdx = STEPS.findIndex((s) => s.key === step);
  const currentLabel = STEPS.find((s) => s.key === step)?.label ?? step;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-white font-medium">{currentLabel}</span>
          <span className="text-slate-400 tabular-nums">{percent}%</span>
        </div>
        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      {/* Step dots */}
      <div className="grid grid-cols-3 gap-2">
        {STEPS.filter((s) => s.key !== "complete").map((s, idx) => {
          const done = idx < currentIdx;
          const active = idx === currentIdx;
          return (
            <div
              key={s.key}
              className={`flex items-center gap-1.5 text-xs ${
                done ? "text-green-400" : active ? "text-blue-400" : "text-slate-600"
              }`}
            >
              {done ? (
                <CheckCircle2 size={12} className="flex-shrink-0" />
              ) : active ? (
                <Loader2 size={12} className="flex-shrink-0 animate-spin" />
              ) : (
                <Circle size={12} className="flex-shrink-0" />
              )}
              <span className="truncate">{s.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
