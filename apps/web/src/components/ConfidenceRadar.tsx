import React from "react";
import { AutonomyBadge } from "./AutonomyBadge";

interface Props {
  confidence: number;
  autonomyLevel: string;
  factorScores?: Record<string, number>;
}

export function ConfidenceRadar({ confidence, autonomyLevel, factorScores = {} }: Props) {
  const pct = Math.round(confidence * 100);

  const factors = [
    {
      name: "Reason Clarity",
      weight: "35%",
      score: factorScores["reason_clarity"] ?? 0.85,
      desc: "Telemetry precision, specific error codes & contradiction checks",
    },
    {
      name: "Historical Pattern",
      weight: "25%",
      score: factorScores["historical_pattern"] ?? 0.90,
      desc: "Customer cohort LTV, past recovery rate & mandate history",
    },
    {
      name: "Context Completeness",
      weight: "20%",
      score: factorScores["context_completeness"] ?? 0.95,
      desc: "Customer language, script, profile & transaction metadata",
    },
    {
      name: "Action History",
      weight: "10%",
      score: factorScores["action_history"] ?? 0.80,
      desc: "Retry progression penalties & past attempt outcomes",
    },
    {
      name: "Model Self-Assessment",
      weight: "10%",
      score: factorScores["model_assessment"] ?? confidence,
      desc: "Raw diagnostic confidence emitted by AI provider",
    },
  ];

  return (
    <div className="rounded-xl bg-white border border-slate-200 p-5 shadow-xs">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            Confidence Calibration
          </span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-2xl font-black text-slate-900 font-mono">{pct}%</span>
            <span className="text-xs text-slate-500 font-medium">Calibrated Score</span>
          </div>
        </div>
        <AutonomyBadge level={autonomyLevel} size="md" />
      </div>

      {/* Progress Bars for the 5 Weighted Dimensions */}
      <div className="mt-4 space-y-3.5">
        {factors.map((f, idx) => {
          const factorPct = Math.round(f.score * 100);
          return (
            <div key={idx} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-slate-800 text-xs">{f.name}</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-mono">
                    w: {f.weight}
                  </span>
                </div>
                <span className="font-mono text-slate-900 font-bold text-xs">{factorPct}%</span>
              </div>

              {/* Bar */}
              <div className="w-full h-2 rounded-full bg-slate-100 border border-slate-200 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    factorPct >= 85
                      ? "bg-emerald-600"
                      : factorPct >= 60
                      ? "bg-amber-500"
                      : "bg-rose-500"
                  }`}
                  style={{ width: `${factorPct}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-500">{f.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
