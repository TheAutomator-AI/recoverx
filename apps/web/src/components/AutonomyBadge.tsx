import React from "react";
import { AutonomyLevel } from "@/lib/types";
import { ShieldCheck, UserCheck, AlertTriangle } from "lucide-react";

interface Props {
  level: AutonomyLevel | string;
  size?: "sm" | "md" | "lg";
}

export function AutonomyBadge({ level, size = "md" }: Props) {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-[11px]",
    md: "px-2.5 py-1 text-xs",
    lg: "px-3 py-1.5 text-xs font-semibold",
  }[size];

  if (level === "AUTONOMOUS") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 font-semibold rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 ${sizeClasses}`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
        AUTONOMOUS
      </span>
    );
  }

  if (level === "ASSISTED") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 font-semibold rounded-md bg-amber-50 text-amber-800 border border-amber-200 ${sizeClasses}`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
        ASSISTED
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-semibold rounded-md bg-rose-50 text-rose-800 border border-rose-200 ${sizeClasses}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-rose-600" />
      ESCALATED
    </span>
  );
}
