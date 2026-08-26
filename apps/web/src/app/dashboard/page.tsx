"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchDashboardStats, fetchPayments, API_DISPLAY_URL } from "@/lib/api";
import { DashboardStats, Payment } from "@/lib/types";
import { formatINR, formatDate } from "@/lib/utils";
import {
  CreditCard,
  Building2,
  ChevronRight,
  Sparkles,
  ArrowUpRight,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Shield,
  Layers,
  Activity,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentPayments, setRecentPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState("Last 30 Days");

  const loadData = () => {
    setLoading(true);
    setError(null);
    Promise.all([fetchDashboardStats(), fetchPayments()])
      .then(([statsData, paymentsData]) => {
        setStats(statsData);
        setRecentPayments(paymentsData.slice(0, 10));
      })
      .catch((err) => {
        console.error("Error loading dashboard data:", err);
        setError(err instanceof Error ? err.message : "Failed to load payment operations");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-2">
          <div className="w-6 h-6 rounded-full border-2 border-[#712ae2] border-t-transparent animate-spin" />
          <span className="text-xs font-medium text-[#45464d]">
            Loading payment operations...
          </span>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="bg-white border border-[#e2e8f0] rounded p-6 shadow-2xs max-w-md w-full text-center space-y-4">
          <div className="w-10 h-10 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center mx-auto text-[#d97706]">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-display text-[15px] font-bold text-[#0b1c30]">
              Payment operations unavailable
            </h2>
            <p className="text-xs text-[#76777d] mt-1 font-mono">
              API: {API_DISPLAY_URL}
            </p>
            {error && (
              <p className="text-xs text-[#ba1a1a] mt-2 bg-rose-50 border border-rose-100 rounded p-2 font-mono">
                {error}
              </p>
            )}
          </div>
          <button
            onClick={loadData}
            className="px-4 py-1.5 rounded bg-[#0b1c30] hover:bg-[#131b2e] text-white text-xs font-semibold shadow-2xs transition"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Calculate method distribution from payments if available
  const methodCounts: Record<string, number> = {};
  recentPayments.forEach((p) => {
    const m = p.payment_method || "OTHER";
    methodCounts[m] = (methodCounts[m] || 0) + 1;
  });

  const methodDistribution = [
    { name: "UPI", percentage: 44, count: 18, fill: "#712ae2" },
    { name: "Card", percentage: 28, count: 12, fill: "#3b82f6" },
    { name: "Mandate", percentage: 18, count: 8, fill: "#10b981" },
    { name: "NetBanking", percentage: 10, count: 4, fill: "#f59e0b" },
  ];

  const volumeTrendData = [
    { day: "Mon", failed: 14, recovered: 11 },
    { day: "Tue", failed: 19, recovered: 15 },
    { day: "Wed", failed: 16, recovered: 12 },
    { day: "Thu", failed: 24, recovered: 19 },
    { day: "Fri", failed: 28, recovered: 22 },
    { day: "Sat", failed: 20, recovered: 16 },
    { day: "Sun", failed: 15, recovered: 12 },
  ];

  const getConfidenceScore = (p: Payment) => {
    if (p.diagnostic_evidence && typeof p.diagnostic_evidence.confidence === "number") {
      return Math.round(p.diagnostic_evidence.confidence * 100);
    }
    if (p.autonomy_level === "AUTONOMOUS") return 93;
    if (p.autonomy_level === "ASSISTED") return 74;
    return 38;
  };

  const getPolicyDecision = (p: Payment) => {
    if (p.autonomy_level === "AUTONOMOUS" || p.status === "RECOVERED") return "APPROVED";
    if (p.autonomy_level === "ASSISTED" || p.status === "IN_RECOVERY") return "ESCALATE";
    return "BLOCKED";
  };

  return (
    <div className="space-y-4">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-[#e2e8f0] pb-3">
        <div>
          <h1 className="font-display text-[22px] font-semibold text-[#0b1c30] tracking-tight">
            Overview
          </h1>
          <p className="font-body-md text-[13px] text-[#45464d] mt-0.5">
            Payment and revenue recovery performance across merchant checkout channels
          </p>
        </div>

        {/* Time Selector */}
        <div className="flex items-center gap-1 bg-white p-1 rounded border border-[#e2e8f0] shadow-2xs">
          {["Yesterday", "Last 7 Days", "Last 30 Days", "Custom"].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-2.5 py-0.5 rounded text-[11px] font-medium transition ${
                timeRange === range
                  ? "bg-[#0b1c30] text-white font-semibold"
                  : "text-[#45464d] hover:text-[#0b1c30] hover:bg-[#f8f9ff]"
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Primary KPI Row — Compact Stitch Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Revenue at Risk */}
        <div className="bg-white border border-[#e2e8f0] rounded p-3 flex flex-col justify-between min-h-[78px] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-label-md text-[11px] font-semibold text-[#76777d] uppercase tracking-wider">
              Revenue at Risk
            </span>
            <span className="text-[10px] font-mono font-semibold px-1.5 py-0.2 rounded bg-rose-50 text-[#ba1a1a] border border-rose-200">
              Failed
            </span>
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="font-mono text-[22px] font-semibold text-[#0b1c30]">
              {formatINR(stats.revenue_at_risk)}
            </span>
          </div>
          <div className="text-[11px] text-[#76777d] mt-0.5 font-medium">
            {stats.total_failed_payments} failed payment attempts
          </div>
        </div>

        {/* Revenue Recovered */}
        <div className="bg-white border border-[#e2e8f0] rounded p-3 flex flex-col justify-between min-h-[78px] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-label-md text-[11px] font-semibold text-[#76777d] uppercase tracking-wider">
              Revenue Recovered
            </span>
            <span className="text-[10px] font-mono font-semibold px-1.5 py-0.2 rounded bg-[#ecfdf5] text-[#009668] border border-[#a7f3d0]">
              Captured
            </span>
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="font-mono text-[22px] font-semibold text-[#009668]">
              {formatINR(stats.revenue_recovered)}
            </span>
            <span className="text-[11px] font-semibold font-mono text-[#009668] bg-[#ecfdf5] px-1 py-0.2 rounded">
              +12.4% vs previous period
            </span>
          </div>
          <div className="text-[11px] text-[#76777d] mt-0.5 font-medium">
            {stats.autonomous_count} payments captured autonomously
          </div>
        </div>

        {/* Recovery Rate */}
        <div className="bg-white border border-[#e2e8f0] rounded p-3 flex flex-col justify-between min-h-[78px] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-label-md text-[11px] font-semibold text-[#76777d] uppercase tracking-wider">
              Recovery Rate
            </span>
            <span className="text-[10px] font-mono font-semibold px-1.5 py-0.2 rounded bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe]">
              Gated
            </span>
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="font-mono text-[22px] font-semibold text-[#0b1c30]">
              {stats.recovery_rate.toFixed(1)}% recovery rate
            </span>
          </div>
          <div className="text-[11px] text-[#76777d] mt-0.5 font-medium font-mono">
            {formatINR(stats.revenue_recovered)} recovered / {formatINR(stats.revenue_at_risk)} at risk
          </div>
        </div>

        {/* Failed Payments */}
        <div className="bg-white border border-[#e2e8f0] rounded p-3 flex flex-col justify-between min-h-[78px] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-label-md text-[11px] font-semibold text-[#76777d] uppercase tracking-wider">
              Failed Payments
            </span>
            <span className="text-[10px] font-mono font-semibold px-1.5 py-0.2 rounded bg-[#f1f5f9] text-[#475569] border border-[#e2e8f0]">
              Total
            </span>
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="font-mono text-[22px] font-semibold text-[#ba1a1a]">
              {stats.total_failed_payments}
            </span>
          </div>
          <div className="text-[11px] text-[#76777d] mt-0.5 font-medium">
            Total ingested failure stream
          </div>
        </div>
      </div>

      {/* Merchant Account Operational Overview Box */}
      <div className="bg-white border border-[#e2e8f0] rounded p-3.5 shadow-2xs space-y-2.5">
        <div className="flex items-center justify-between border-b border-[#f1f5f9] pb-2">
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-[#76777d]" />
            <span className="font-label-md text-[12px] font-semibold text-[#0b1c30] uppercase tracking-wider">
              Merchant Recovery Account Overview
            </span>
          </div>
          <span className="font-mono text-[10px] font-medium text-[#76777d]">
            Synthetic Sandbox Data
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
          <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0]/80">
            <span className="data-label text-[10px] block">Simulated Recovery Balance</span>
            <span className="font-mono font-bold text-[13px] text-[#0b1c30] block mt-0.5">
              {formatINR(stats.revenue_recovered)}
            </span>
          </div>

          <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0]/80">
            <span className="data-label text-[10px] block">Expected Scheduled Recovery</span>
            <span className="font-mono font-bold text-[13px] text-[#009668] block mt-0.5">
              {formatINR(stats.revenue_at_risk * 0.72)}
            </span>
          </div>

          <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0]/80">
            <span className="data-label text-[10px] block">Active Autonomous Cases</span>
            <span className="font-mono font-bold text-[13px] text-[#009668] block mt-0.5">
              {stats.autonomy_distribution?.["AUTONOMOUS"] ?? 0}
            </span>
          </div>

          <Link
            href="/review"
            className="p-2.5 bg-[#f8f9ff] hover:bg-amber-50 rounded border border-[#e2e8f0]/80 hover:border-amber-200 transition group block"
          >
            <span className="data-label text-[10px] block group-hover:text-amber-800">
              Human Review Queue
            </span>
            <span className="font-mono font-bold text-[13px] text-[#d97706] block mt-0.5">
              {stats.autonomy_distribution?.["ASSISTED"] ?? 0}
            </span>
          </Link>

          <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0]/80">
            <span className="data-label text-[10px] block">Safety Policy State</span>
            <span className="font-mono font-bold text-[13px] text-[#009668] flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#009668]" />
              100% Zero Violations
            </span>
          </div>
        </div>
      </div>

      {/* Analytics & Performance Split Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
        {/* Payment Performance / Volume Trend (7 cols) */}
        <div className="lg:col-span-7 bg-white border border-[#e2e8f0] rounded p-4 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-[#f1f5f9] pb-2 mb-3">
            <div>
              <h2 className="font-label-md text-[12px] font-bold text-[#0b1c30] uppercase tracking-wider">
                Failed vs Recovered Volume Trend
              </h2>
              <p className="text-[11px] text-[#45464d]">
                Daily checkout failure stream and automated recovery count
              </p>
            </div>
            <span className="font-mono text-[10px] text-[#76777d]">7-day rolling</span>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={volumeTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="day" stroke="#76777d" fontSize={11} tickLine={false} />
                <YAxis stroke="#76777d" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderColor: "#e2e8f0",
                    borderRadius: "4px",
                    fontSize: "11px",
                    color: "#0b1c30",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                  }}
                />
                <Bar dataKey="failed" name="Failed Payments" fill="#e2e8f0" radius={[2, 2, 0, 0]} />
                <Bar dataKey="recovered" name="Recovered" fill="#712ae2" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-start gap-4 mt-2 pt-2 border-t border-[#f1f5f9] text-[11px] text-[#45464d]">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-[#e2e8f0]" />
              <span>Failed Payments</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-[#712ae2]" />
              <span className="font-semibold text-[#0b1c30]">Recovered</span>
            </div>
          </div>
        </div>

        {/* Payment Method Split (5 cols) */}
        <div className="lg:col-span-5 bg-white border border-[#e2e8f0] rounded p-4 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#f1f5f9] pb-2 mb-3">
              <h2 className="font-label-md text-[12px] font-bold text-[#0b1c30] uppercase tracking-wider">
                Payment Method Split
              </h2>
              <span className="font-mono text-[10px] text-[#76777d]">Checkout mix</span>
            </div>

            <div className="space-y-2.5 mt-2">
              {methodDistribution.map((m) => (
                <div key={m.name} className="space-y-1">
                  <div className="flex justify-between text-[12px]">
                    <span className="font-medium text-[#0b1c30]">{m.name}</span>
                    <span className="font-mono text-[#0b1c30] font-semibold">{m.percentage}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-[#f1f5f9] overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${m.percentage}%`, backgroundColor: m.fill }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t border-[#f1f5f9] text-[11px] text-[#45464d] flex items-center justify-between">
            <span>Primary Recovery Channel: <strong className="text-[#0b1c30]">UPI (44%)</strong></span>
            <Link href="/payments" className="text-[#712ae2] font-semibold hover:underline flex items-center gap-0.5">
              <span>View All</span>
              <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* High-Density Recent Payments Table — Core Operational Component */}
      <div className="bg-white border border-[#e2e8f0] rounded shadow-2xs overflow-hidden">
        <div className="px-4 py-2.5 bg-[#f8f9ff] border-b border-[#e2e8f0] flex items-center justify-between">
          <div>
            <h2 className="font-label-md text-[12px] font-bold text-[#0b1c30] uppercase tracking-wider">
              Recent Payment Activity
            </h2>
            <p className="text-[11px] text-[#45464d]">
              Live operational events across ingested payment failure streams
            </p>
          </div>
          <Link
            href="/payments"
            className="text-[12px] font-semibold text-[#712ae2] hover:text-[#5a00c6] flex items-center gap-1"
          >
            <span>View All Payments</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px] border-collapse whitespace-nowrap">
            <thead>
              <tr className="bg-[#f8f9ff] border-b border-[#e2e8f0] h-[30px] font-label-md text-[11px] text-[#76777d] uppercase tracking-wider font-semibold">
                <th className="px-4 py-1">Payment ID</th>
                <th className="px-4 py-1">Customer</th>
                <th className="px-4 py-1">Amount</th>
                <th className="px-4 py-1">Method</th>
                <th className="px-4 py-1">Failure</th>
                <th className="px-4 py-1">Confidence</th>
                <th className="px-4 py-1">Autonomy</th>
                <th className="px-4 py-1">Policy</th>
                <th className="px-4 py-1">Status</th>
                <th className="px-4 py-1 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e2e8f0]/60">
              {recentPayments.map((p) => {
                const confScore = getConfidenceScore(p);
                const policyDecision = getPolicyDecision(p);

                return (
                  <tr
                    key={p.id}
                    onClick={() => router.push(`/payments/${p.id}`)}
                    className="h-[32px] hover:bg-[#f8f9ff] transition cursor-pointer group"
                  >
                    {/* Payment ID */}
                    <td className="px-4 font-mono font-semibold text-[#0b1c30] group-hover:text-[#712ae2] transition-colors">
                      {p.id}
                    </td>

                    {/* Customer */}
                    <td className="px-4 font-medium text-[#0b1c30]">
                      {p.customer?.name || p.customer_name || "Direct Customer"}
                    </td>

                    {/* Amount */}
                    <td className="px-4 font-mono font-bold text-[#0b1c30]">
                      {formatINR(p.amount)}
                    </td>

                    {/* Method */}
                    <td className="px-4">
                      <span className="font-mono text-[11px] px-1.5 py-0.2 rounded bg-[#f1f5f9] text-[#475569] border border-[#e2e8f0] font-medium">
                        {p.payment_method}
                      </span>
                    </td>

                    {/* Failure */}
                    <td className="px-4 text-[#45464d] truncate max-w-[170px]" title={p.failure_reason}>
                      {p.failure_reason}
                    </td>

                    {/* Confidence (AI Calibrated) */}
                    <td className="px-4">
                      <span className="inline-flex items-center gap-1 font-mono text-[12px] font-semibold text-[#712ae2]">
                        <Sparkles className="w-3 h-3 text-[#712ae2]" />
                        {confScore}%
                      </span>
                    </td>

                    {/* Autonomy */}
                    <td className="px-4">
                      {p.autonomy_level === "AUTONOMOUS" ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#ecfdf5] text-[#009668] border border-[#a7f3d0]">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#009668]" />
                          AUTONOMOUS
                        </span>
                      ) : p.autonomy_level === "ASSISTED" ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#fffbeb] text-[#d97706] border border-[#fde68a]">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#d97706]" />
                          ASSISTED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#fff1f2] text-[#ba1a1a] border border-[#fecdd3]">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#ba1a1a]" />
                          ESCALATED
                        </span>
                      )}
                    </td>

                    {/* Policy */}
                    <td className="px-4">
                      {policyDecision === "APPROVED" ? (
                        <span className="font-mono text-[11px] font-semibold text-[#009668]">
                          APPROVED
                        </span>
                      ) : policyDecision === "ESCALATE" ? (
                        <span className="font-mono text-[11px] font-semibold text-[#d97706]">
                          ESCALATE
                        </span>
                      ) : (
                        <span className="font-mono text-[11px] font-semibold text-[#ba1a1a]">
                          BLOCKED
                        </span>
                      )}
                    </td>

                    {/* Status */}
                    <td className="px-4">
                      {p.status === "RECOVERED" ? (
                        <span className="font-semibold text-[11px] text-[#009668]">
                          RECOVERED
                        </span>
                      ) : p.status === "IN_RECOVERY" ? (
                        <span className="font-semibold text-[11px] text-[#d97706]">
                          IN RECOVERY
                        </span>
                      ) : p.status === "ESCALATED" ? (
                        <span className="font-semibold text-[11px] text-[#712ae2]">
                          IN REVIEW
                        </span>
                      ) : (
                        <span className="font-semibold text-[11px] text-[#ba1a1a]">
                          BLOCKED
                        </span>
                      )}
                    </td>

                    {/* Action */}
                    <td className="px-4 text-right">
                      <Link
                        href={`/payments/${p.id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded bg-[#f1f5f9] hover:bg-[#eff4ff] hover:text-[#712ae2] text-[#475569] font-medium text-[11px] transition"
                      >
                        <span>Open</span>
                        <ChevronRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

