import React from "react";
import { PolicyDecisionType } from "@/lib/types";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";

interface Props {
  decision: PolicyDecisionType | string;
}

export function PolicyStatusBadge({ decision }: Props) {
  if (decision === "APPROVE") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        POLICY APPROVED
      </span>
    );
  }

  if (decision === "BLOCK") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200">
        <XCircle className="w-3.5 h-3.5 text-rose-600" />
        POLICY BLOCKED
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-indigo-50 text-indigo-800 border border-indigo-200">
      <AlertCircle className="w-3.5 h-3.5 text-indigo-600" />
      POLICY ESCALATED
    </span>
  );
}
