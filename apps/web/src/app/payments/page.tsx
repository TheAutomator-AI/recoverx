"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchPayments } from "@/lib/api";
import { Payment } from "@/lib/types";
import { formatINR, formatDate } from "@/lib/utils";
import { HumanReviewDrawer } from "@/components/HumanReviewDrawer";
import {
  Search,
  Download,
  ChevronRight,
  Sparkles,
  UserCheck,
  ChevronLeft,
  Filter,
} from "lucide-react";

export default function PaymentsPage() {
  const router = useRouter();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [methodFilter, setMethodFilter] = useState("ALL");
  const [failureFilter, setFailureFilter] = useState("ALL");
  const [selectedReviewPayment, setSelectedReviewPayment] = useState<Payment | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const loadPayments = () => {
    setLoading(true);
    fetchPayments()
      .then((data) => setPayments(data))
      .catch((err) => console.error("Error fetching payments:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadPayments();
  }, []);

  const filteredPayments = payments.filter((p) => {
    const matchesStatus = statusFilter === "ALL" || p.status === statusFilter;
    const matchesMethod = methodFilter === "ALL" || p.payment_method === methodFilter;
    const matchesFailure =
      failureFilter === "ALL" ||
      p.failure_reason.toLowerCase().includes(failureFilter.toLowerCase()) ||
      p.failure_step.toLowerCase().includes(failureFilter.toLowerCase());
    const q = searchTerm.toLowerCase();
    const matchesSearch =
      p.id.toLowerCase().includes(q) ||
      p.order_id.toLowerCase().includes(q) ||
      p.failure_reason.toLowerCase().includes(q) ||
      (p.customer?.name && p.customer.name.toLowerCase().includes(q)) ||
      (p.customer_name && p.customer_name.toLowerCase().includes(q));
    return matchesStatus && matchesMethod && matchesFailure && matchesSearch;
  });

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

  const handleOpenDrawer = (e: React.MouseEvent, p: Payment) => {
    e.stopPropagation();
    setSelectedReviewPayment(p);
    setDrawerOpen(true);
  };

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-[#e2e8f0] pb-3">
        <div>
          <h1 className="font-display text-[22px] font-semibold text-[#0b1c30] tracking-tight">
            Payments
          </h1>
          <p className="font-body-md text-[13px] text-[#45464d] mt-0.5">
            Payment activity and recovery state
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {}}
            className="h-8 px-3 bg-white border border-[#e2e8f0] text-[#0b1c30] hover:bg-[#f8f9ff] text-[12px] font-medium rounded flex items-center gap-1.5 shadow-2xs transition"
          >
            <Download className="w-3.5 h-3.5 text-[#76777d]" />
            <span>Export List</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar (Stitch High-Density Specs) */}
      <div className="border border-[#e2e8f0] bg-white rounded p-2 flex flex-wrap items-center gap-2 shadow-2xs">
        {/* Search */}
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search className="w-3.5 h-3.5 text-[#76777d] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by ID, Customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-7 pl-8 pr-3 bg-[#f8f9ff] border border-[#e2e8f0] rounded text-[12px] placeholder:text-[#76777d] focus:border-[#712ae2] focus:ring-1 focus:ring-[#712ae2] outline-none transition"
          />
        </div>

        <div className="w-px h-5 bg-[#e2e8f0] hidden sm:block mx-1" />

        {/* Method Filter */}
        <select
          value={methodFilter}
          onChange={(e) => setMethodFilter(e.target.value)}
          className="h-7 px-2.5 border border-[#e2e8f0] rounded bg-[#f8f9ff] text-[#0b1c30] text-[12px] font-medium focus:border-[#712ae2] outline-none"
        >
          <option value="ALL">All Methods</option>
          <option value="UPI">UPI</option>
          <option value="CARD">Card</option>
          <option value="NETBANKING">NetBanking</option>
          <option value="MANDATE_AUTOPAY">Mandate</option>
        </select>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-7 px-2.5 border border-[#e2e8f0] rounded bg-[#f8f9ff] text-[#0b1c30] text-[12px] font-medium focus:border-[#712ae2] outline-none"
        >
          <option value="ALL">All Statuses</option>
          <option value="RECOVERED">Recovered</option>
          <option value="IN_RECOVERY">In Recovery</option>
          <option value="ESCALATED">Escalated</option>
          <option value="FAILED">Failed</option>
          <option value="TERMINAL_FAILED">Terminal Failed</option>
        </select>

        {/* Failure Type Filter */}
        <select
          value={failureFilter}
          onChange={(e) => setFailureFilter(e.target.value)}
          className="h-7 px-2.5 border border-[#e2e8f0] rounded bg-[#f8f9ff] text-[#0b1c30] text-[12px] font-medium focus:border-[#712ae2] outline-none"
        >
          <option value="ALL">All Failures</option>
          <option value="timeout">Timeout</option>
          <option value="balance">Insufficient Funds</option>
          <option value="telemetry">Contradictory Telemetry</option>
          <option value="auth">Auth / OTP Expired</option>
        </select>

        {(searchTerm || statusFilter !== "ALL" || methodFilter !== "ALL" || failureFilter !== "ALL") && (
          <button
            onClick={() => {
              setSearchTerm("");
              setStatusFilter("ALL");
              setMethodFilter("ALL");
              setFailureFilter("ALL");
            }}
            className="text-[11px] text-[#712ae2] font-semibold hover:underline ml-auto pr-2"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* High-Density Data Table */}
      <div className="bg-white border border-[#e2e8f0] rounded shadow-2xs overflow-hidden">
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
                <th className="px-4 py-1">Created</th>
                <th className="px-4 py-1 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e2e8f0]/60">
              {loading ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-[#76777d]">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-6 h-6 rounded-full border-2 border-[#712ae2] border-t-transparent animate-spin" />
                      <span className="text-xs font-medium">Loading payments ledger...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredPayments.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-[#76777d] text-xs">
                    No payment records found matching your filters.
                  </td>
                </tr>
              ) : (
                filteredPayments.map((p) => {
                  const confScore = getConfidenceScore(p);
                  const policyDecision = getPolicyDecision(p);
                  const isReviewable = p.autonomy_level === "ASSISTED" || p.status === "ESCALATED";

                  return (
                    <tr
                      key={p.id}
                      onClick={() => router.push(`/payments/${p.id}`)}
                      className={`h-[32px] hover:bg-[#f8f9ff] transition cursor-pointer group ${
                        p.status === "TERMINAL_FAILED" || p.autonomy_level === "ESCALATED"
                          ? "border-l-2 border-l-[#ba1a1a]"
                          : ""
                      }`}
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

                      {/* Failure Reason */}
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

                      {/* Created */}
                      <td className="px-4 text-[#76777d] font-mono text-[11px]">
                        {formatDate(p.created_at)}
                      </td>

                      {/* Actions */}
                      <td className="px-4 text-right">
                        <div className="inline-flex items-center gap-1">
                          {isReviewable && (
                            <button
                              onClick={(e) => handleOpenDrawer(e, p)}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#eff4ff] hover:bg-[#d3e4fe] text-[#712ae2] font-semibold text-[11px] transition border border-[#d3e4fe]"
                              title="Open Intervention Drawer"
                            >
                              <UserCheck className="w-3 h-3" />
                              <span>Review</span>
                            </button>
                          )}
                          <Link
                            href={`/payments/${p.id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded bg-[#f1f5f9] hover:bg-[#eff4ff] hover:text-[#712ae2] text-[#475569] font-medium text-[11px] transition"
                          >
                            <span>Open</span>
                            <ChevronRight className="w-3 h-3" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="h-9 border-t border-[#e2e8f0] flex items-center justify-between px-4 bg-[#f8f9ff] text-[11px] text-[#76777d]">
          <span>Showing 1-{filteredPayments.length} of {payments.length} transactions</span>
          <div className="flex items-center gap-1.5">
            <button
              disabled
              aria-label="Previous Page"
              className="w-6 h-6 flex items-center justify-center rounded border border-[#e2e8f0] bg-white text-[#76777d] disabled:opacity-40"
            >
              <ChevronLeft className="w-3 h-3" />
            </button>
            <button
              disabled
              aria-label="Next Page"
              className="w-6 h-6 flex items-center justify-center rounded border border-[#e2e8f0] bg-white text-[#76777d] disabled:opacity-40"
            >
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Human Review Drawer */}
      <HumanReviewDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        payment={selectedReviewPayment}
        onActionComplete={loadPayments}
      />
    </div>
  );
}

