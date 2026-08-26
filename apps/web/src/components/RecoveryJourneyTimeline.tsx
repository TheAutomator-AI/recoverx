import React, { useState } from "react";
import { JourneyStep } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Cpu,
  ShieldCheck,
  Zap,
  CheckCheck,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface Props {
  steps: JourneyStep[];
}

export function RecoveryJourneyTimeline({ steps }: Props) {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  const getStepIcon = (name: string, status: string) => {
    if (status === "FAILED" || status === "BLOCKED") {
      return <XCircle className="w-4 h-4 text-rose-600" />;
    }
    switch (name) {
      case "FAILED":
        return <XCircle className="w-4 h-4 text-rose-600" />;
      case "DIAGNOSED":
        return <Cpu className="w-4 h-4 text-indigo-600" />;
      case "CONFIDENCE_CALCULATED":
        return <Zap className="w-4 h-4 text-amber-600" />;
      case "POLICY_CHECK":
        return <ShieldCheck className="w-4 h-4 text-emerald-600" />;
      case "ACTION_EXECUTED":
        return <Clock className="w-4 h-4 text-blue-600" />;
      case "OUTCOME":
        return <CheckCheck className="w-4 h-4 text-emerald-600" />;
      default:
        return <CheckCircle2 className="w-4 h-4 text-slate-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-50 text-emerald-800 border border-emerald-200">COMPLETED</span>;
      case "BLOCKED":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-rose-50 text-rose-800 border border-rose-200">BLOCKED</span>;
      case "ESCALATED":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-indigo-50 text-indigo-800 border border-indigo-200">ESCALATED</span>;
      case "ACTIVE":
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-blue-50 text-blue-800 border border-blue-200">ACTIVE</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-slate-100 text-slate-700">{status}</span>;
    }
  };

  return (
    <div className="space-y-3">
      <div className="relative pl-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {steps.map((step, idx) => {
          const isExpanded = expandedStep === idx;
          return (
            <div key={idx} className="relative mb-4 last:mb-0 group">
              {/* Step indicator node */}
              <div className="absolute -left-6 top-1 flex items-center justify-center w-5 h-5 rounded-full bg-white border border-slate-300 shadow-2xs">
                {getStepIcon(step.step_name, step.status)}
              </div>

              {/* Step Card */}
              <div className="ml-2 rounded-lg bg-white border border-slate-200 p-3.5 hover:border-slate-300 transition-all shadow-2xs">
                <div
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => setExpandedStep(isExpanded ? null : idx)}
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                        {step.actor}
                      </span>
                      {getStatusBadge(step.status)}
                    </div>
                    <h4 className="text-xs font-bold text-slate-900">{step.title}</h4>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-slate-400 font-mono">
                      {formatDate(step.timestamp)}
                    </span>
                    <button className="text-slate-400 hover:text-slate-600 transition">
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Collapsible Details */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-100">
                    <pre className="p-3 rounded-md bg-slate-50 text-slate-800 font-mono text-[11px] overflow-x-auto border border-slate-200">
                      {JSON.stringify(step.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
