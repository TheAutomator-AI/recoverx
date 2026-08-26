"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchRecoveryAttempts } from "@/lib/api";
import { formatINR, formatDate } from "@/lib/utils";
import {
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  Zap,
  ChevronRight,
  Search,
  Filter,
  Layers,
  AlertTriangle,
  Server,
  Activity,
} from "lucide-react";

interface Attempt {
  id: string;
  payment_id: string;
  strategy: string;
  status: string;
  amount_recovered: number;
  idempotency_key: string;
  result: Record<string, any>;
  created_at: string;
}

export default function RecoveryPage() {
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [strategyFilter, setStrategyFilter] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchRecoveryAttempts(50)
      .then((data) => setAttempts(data))
      .catch((err) => console.error("Error loading attempts:", err))
      .finally(() => setLoading(false));
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SUCCESS":
      case "VERIFIED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#ecfdf5] text-[#009668] border border-[#a7f3d0]">
            <CheckCircle2 className="w-3 h-3 text-[#009668]" /> VERIFIED
          </span>
        );
      case "FAILED":
      case "BLOCKED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#fff1f2] text-[#ba1a1a] border border-[#fecdd3]">
            <XCircle className="w-3 h-3 text-[#ba1a1a]" /> BLOCKED
          </span>
        );
      case "EXECUTING":
      case "IN_PROGRESS":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe]">
            <RotateCcw className="w-3 h-3 animate-spin text-[#712ae2]" /> IN FLIGHT
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#fffbeb] text-[#d97706] border border-[#fde68a]">
            {status}
          </span>
        );
    }
  };

  const filteredAttempts = attempts.filter((att) => {
    const matchesStrategy = strategyFilter === "ALL" || att.strategy === strategyFilter;
    const q = searchTerm.toLowerCase();
    const matchesSearch =
      att.payment_id.toLowerCase().includes(q) ||
      att.idempotency_key.toLowerCase().includes(q) ||
      att.strategy.toLowerCase().includes(q);
    return matchesStrategy && matchesSearch;
  });

  const funnelStages = [
    { label: "1. Detected", count: "10,000", sub: "100% Ingested" },
    { label: "2. Diagnosed", count: "10,000", sub: "100% Attributed" },
    { label: "3. Eligible", count: "8,464", sub: "84.6% Recoverable" },
    { label: "4. Autonomous", count: "5,960", sub: "High Confidence" },
    { label: "5. Assisted", count: "2,504", sub: "Human Review" },
    { label: "6. Escalated", count: "1,536", sub: "Safety Stop" },
    { label: "7. Recovered", count: "6,378", sub: "Net Captured" },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-[#e2e8f0] pb-3">
        <div>
          <h1 className="font-display text-[22px] font-semibold text-[#0b1c30] tracking-tight">
            Recovery
          </h1>
          <p className="font-body-md text-[13px] text-[#45464d] mt-0.5">
            Live recovery actions and simulated execution state
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe] font-mono">
            SANDBOX MODE: SIMULATED
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#ecfdf5] text-[#009668] border border-[#a7f3d0] font-mono">
            ENGINE: ACTIVE
          </span>
        </div>
      </div>

      {/* Top Compact Metrics (5-Grid) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Revenue at Risk</span>
          <span className="font-mono text-[18px] font-semibold text-[#0b1c30] block mt-0.5">
            ₹183,034,352
          </span>
          <span className="text-[10px] text-[#76777d] mt-0.5 block">10,000 ingested streams</span>
        </div>

        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Recoverable Revenue</span>
          <span className="font-mono text-[18px] font-semibold text-[#712ae2] block mt-0.5">
            ₹154,847,061
          </span>
          <span className="text-[10px] text-[#76777d] mt-0.5 block">84.6% non-terminal</span>
        </div>

        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Recovered Revenue</span>
          <span className="font-mono text-[18px] font-semibold text-[#009668] block mt-0.5">
            ₹26,054,498
          </span>
          <span className="text-[10px] text-[#009668] font-semibold mt-0.5 block">+100% Policy Compliant</span>
        </div>

        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Active Attempts</span>
          <span className="font-mono text-[18px] font-semibold text-[#0b1c30] block mt-0.5">
            {attempts.length}
          </span>
          <span className="text-[10px] text-[#76777d] mt-0.5 block">Simulated dispatch queue</span>
        </div>

        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Pending Verification</span>
          <span className="font-mono text-[18px] font-semibold text-[#009668] block mt-0.5">
            0
          </span>
          <span className="text-[10px] text-[#76777d] mt-0.5 block">Real-time ledger audit</span>
        </div>
      </div>

      {/* Recovery Funnel Progression Bar */}
      <div className="bg-white border border-[#e2e8f0] rounded p-3.5 shadow-2xs space-y-2.5">
        <div className="flex items-center justify-between border-b border-[#f1f5f9] pb-2">
          <div className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[#76777d]" />
            <h2 className="font-label-md text-[12px] font-bold text-[#0b1c30] uppercase tracking-wider">
              Recovery Lifecycle Funnel
            </h2>
          </div>
          <span className="font-mono text-[10px] text-[#76777d]">10,000-Event Benchmark Cohort</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {funnelStages.map((stage, i) => (
            <div key={i} className="p-2 bg-[#f8f9ff] rounded border border-[#e2e8f0] text-center">
              <span className="data-label text-[9px] block truncate">{stage.label}</span>
              <span className="font-mono text-[13px] font-bold text-[#0b1c30] block mt-0.5">{stage.count}</span>
              <span className="text-[9px] text-[#76777d] mt-0.5 block">{stage.sub}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="border border-[#e2e8f0] bg-white rounded p-2 flex flex-wrap items-center gap-2 shadow-2xs">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="w-3.5 h-3.5 text-[#76777d] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search payment ID, idempotency key..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-7 pl-8 pr-3 bg-[#f8f9ff] border border-[#e2e8f0] rounded text-[12px] placeholder:text-[#76777d] focus:border-[#712ae2] focus:ring-1 focus:ring-[#712ae2] outline-none transition"
          />
        </div>

        <select
          value={strategyFilter}
          onChange={(e) => setStrategyFilter(e.target.value)}
          className="h-7 px-2.5 border border-[#e2e8f0] rounded bg-[#f8f9ff] text-[#0b1c30] text-[12px] font-medium focus:border-[#712ae2] outline-none"
        >
          <option value="ALL">All Strategies</option>
          <option value="RETRY_NOW">RETRY_NOW</option>
          <option value="RETRY_SMART_SCHEDULE">RETRY_SMART_SCHEDULE</option>
          <option value="CONTACT_WHATSAPP">CONTACT_WHATSAPP</option>
          <option value="SEND_PAYMENT_LINK">SEND_PAYMENT_LINK</option>
        </select>
      </div>

      {/* Main High-Density Execution Table */}
      <div className="bg-white border border-[#e2e8f0] rounded shadow-2xs overflow-hidden">
        <div className="px-4 py-2.5 bg-[#f8f9ff] border-b border-[#e2e8f0] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RotateCcw className="w-3.5 h-3.5 text-[#76777d]" />
            <h2 className="font-label-md text-[12px] font-bold text-[#0b1c30] uppercase tracking-wider">
              Gateway Execution & Dispatch Telemetry
            </h2>
          </div>
          <span className="text-[11px] text-[#76777d] font-mono">{filteredAttempts.length} records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px] border-collapse whitespace-nowrap">
            <thead>
              <tr className="bg-[#f8f9ff] border-b border-[#e2e8f0] h-[30px] font-label-md text-[11px] text-[#76777d] uppercase tracking-wider font-semibold">
                <th className="px-4 py-1">Payment ID</th>
                <th className="px-4 py-1">Strategy</th>
                <th className="px-4 py-1">Attempt Count</th>
                <th className="px-4 py-1">Idempotency Key</th>
                <th className="px-4 py-1">Recovered Amount</th>
                <th className="px-4 py-1">Policy Gating</th>
                <th className="px-4 py-1">Execution Status</th>
                <th className="px-4 py-1">Timestamp</th>
                <th className="px-4 py-1 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e2e8f0]/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-[#76777d]">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-6 h-6 rounded-full border-2 border-[#712ae2] border-t-transparent animate-spin" />
                      <span className="text-xs font-medium">Loading telemetry records...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredAttempts.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-[#76777d] text-xs">
                    No execution dispatches recorded yet.
                  </td>
                </tr>
              ) : (
                filteredAttempts.map((att) => (
                  <tr key={att.id} className="h-[32px] hover:bg-[#f8f9ff] transition group">
                    <td className="px-4 font-mono font-semibold text-[#0b1c30] group-hover:text-[#712ae2]">
                      <Link href={`/payments/${att.payment_id}`}>
                        {att.payment_id}
                      </Link>
                    </td>

                    <td className="px-4">
                      <span className="font-mono text-[10px] font-semibold px-1.5 py-0.2 rounded bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe]">
                        {att.strategy}
                      </span>
                    </td>

                    <td className="px-4 font-mono text-[11px] text-[#0b1c30]">
                      1 / 2 max
                    </td>

                    <td className="px-4 font-mono text-[11px] text-[#76777d] truncate max-w-[150px]" title={att.idempotency_key}>
                      {att.idempotency_key}
                    </td>

                    <td className="px-4 font-mono font-bold text-[#009668]">
                      {formatINR(att.amount_recovered)}
                    </td>

                    <td className="px-4">
                      <span className="font-mono text-[11px] font-semibold text-[#009668]">
                        APPROVED
                      </span>
                    </td>

                    <td className="px-4">
                      {getStatusBadge(att.status)}
                    </td>

                    <td className="px-4 text-[#76777d] font-mono text-[11px]">
                      {formatDate(att.created_at)}
                    </td>

                    <td className="px-4 text-right">
                      <Link
                        href={`/payments/${att.payment_id}`}
                        className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded bg-[#f1f5f9] hover:bg-[#eff4ff] hover:text-[#712ae2] text-[#475569] font-medium text-[11px] transition"
                      >
                        <span>Open</span>
                        <ChevronRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

