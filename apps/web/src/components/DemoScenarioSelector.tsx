"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { fetchDemoCase } from "@/lib/api";
import { Loader2 } from "lucide-react";

export function DemoScenarioSelector() {
  const router = useRouter();
  const [loadingCase, setLoadingCase] = useState<string | null>(null);

  const handleSelectCase = async (caseKey: string) => {
    try {
      setLoadingCase(caseKey);
      const res = await fetchDemoCase(caseKey);
      if (res && res.payment_id) {
        router.push(`/payments/${res.payment_id}`);
      }
    } catch (err) {
      console.error("Failed to load demo case", err);
    } finally {
      setLoadingCase(null);
    }
  };

  return (
    <div className="hidden lg:flex items-center gap-1 h-full">
      {/* Case A */}
      <button
        onClick={() => handleSelectCase("case_a")}
        disabled={loadingCase !== null}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[12px] font-medium text-[#45464d] hover:text-[#0b1c30] hover:bg-[#eff4ff] transition disabled:opacity-50"
        title="Load Case A: Autonomous recovery scenario"
      >
        {loadingCase === "case_a" ? (
          <Loader2 className="w-3 h-3 animate-spin text-[#009668]" />
        ) : (
          <span className="w-1.5 h-1.5 rounded-full bg-[#009668]" />
        )}
        <span>Case A — Autonomous</span>
      </button>

      {/* Case B */}
      <button
        onClick={() => handleSelectCase("case_b")}
        disabled={loadingCase !== null}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[12px] font-medium text-[#45464d] hover:text-[#0b1c30] hover:bg-[#eff4ff] transition disabled:opacity-50"
        title="Load Case B: Human review required scenario"
      >
        {loadingCase === "case_b" ? (
          <Loader2 className="w-3 h-3 animate-spin text-[#d97706]" />
        ) : (
          <span className="w-1.5 h-1.5 rounded-full bg-[#d97706]" />
        )}
        <span>Case B — Assisted</span>
      </button>

      {/* Case C */}
      <button
        onClick={() => handleSelectCase("case_c")}
        disabled={loadingCase !== null}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[12px] font-medium text-[#45464d] hover:text-[#0b1c30] hover:bg-[#eff4ff] transition disabled:opacity-50"
        title="Load Case C: Terminal policy block scenario"
      >
        {loadingCase === "case_c" ? (
          <Loader2 className="w-3 h-3 animate-spin text-[#ba1a1a]" />
        ) : (
          <span className="w-1.5 h-1.5 rounded-full bg-[#ba1a1a]" />
        )}
        <span>Case C — Escalated</span>
      </button>
    </div>
  );
}

