"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchPromises, updatePromiseStatus } from "@/lib/api";
import { PromiseToPay } from "@/lib/types";
import { formatINR, formatDate } from "@/lib/utils";
import {
  CalendarClock,
  CheckCircle2,
  AlertTriangle,
  Clock,
  XCircle,
  MessageSquare,
  Search,
  Check,
  X,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Filter,
  User,
  CreditCard,
  Globe,
} from "lucide-react";

export default function PromisesPage() {
  const [promises, setPromises] = useState<PromiseToPay[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const loadPromises = () => {
    setLoading(true);
    fetchPromises()
      .then((data) => setPromises(data))
      .catch((err) => console.error("Error loading promises:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadPromises();
  }, []);

  const handleStatusChange = async (e: React.MouseEvent, promiseId: string, newStatus: string) => {
    e.stopPropagation();
    try {
      await updatePromiseStatus(promiseId, newStatus);
      loadPromises();
    } catch (err) {
      console.error("Error updating status:", err);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "FULFILLED":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#ecfdf5] text-[#009668] border border-[#a7f3d0]">
            <CheckCircle2 className="w-3 h-3 text-[#009668]" /> FULFILLED
          </span>
        );
      case "FOLLOW_UP_DUE":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#fffbeb] text-[#d97706] border border-[#fde68a]">
            <Clock className="w-3 h-3 text-[#d97706]" /> DUE TODAY
          </span>
        );
      case "OVERDUE":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#fff1f2] text-[#ba1a1a] border border-[#fecdd3]">
            <AlertTriangle className="w-3 h-3 text-[#ba1a1a]" /> OVERDUE
          </span>
        );
      case "BROKEN":
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#fff1f2] text-[#ba1a1a] border border-[#fecdd3]">
            <XCircle className="w-3 h-3 text-[#ba1a1a]" /> BROKEN
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe]">
            <CalendarClock className="w-3 h-3 text-[#712ae2]" /> ACTIVE
          </span>
        );
    }
  };

  const filteredPromises = promises.filter((p) => {
    const matchesStatus = statusFilter === "ALL" || p.status === statusFilter;
    const q = searchTerm.toLowerCase();
    const matchesSearch =
      p.payment_id.toLowerCase().includes(q) ||
      (p.message && p.message.toLowerCase().includes(q));
    return matchesStatus && matchesSearch;
  });

  const activeCount = promises.filter((p) => p.status === "PROMISE_TO_PAY" || p.status === "CUSTOMER_CONTACTED").length;
  const dueCount = promises.filter((p) => p.status === "FOLLOW_UP_DUE").length;
  const fulfilledCount = promises.filter((p) => p.status === "FULFILLED").length;
  const overdueCount = promises.filter((p) => p.status === "OVERDUE" || p.status === "BROKEN").length;
  const totalExpectedAmount = promises.reduce((acc, p) => acc + (p.status !== "BROKEN" ? p.amount : 0), 0);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-[#e2e8f0] pb-3">
        <div>
          <h1 className="font-display text-[22px] font-semibold text-[#0b1c30] tracking-tight">
            Promise to Pay
          </h1>
          <p className="font-body-md text-[13px] text-[#45464d] mt-0.5">
            Customer recovery commitments and conversational follow-up
          </p>
        </div>

        <span className="text-[10px] font-mono font-bold text-[#76777d] bg-white border border-[#e2e8f0] px-2.5 py-1 rounded shadow-2xs">
          COLLECTIONS LEDGER
        </span>
      </div>

      {/* Compact Summary Cards (5-Grid) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Active Commitments</span>
          <span className="font-mono text-[18px] font-semibold text-[#712ae2] block mt-0.5">
            {activeCount}
          </span>
          <span className="text-[10px] text-[#76777d] mt-0.5 block">Scheduled pay cycles</span>
        </div>

        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Due Today</span>
          <span className="font-mono text-[18px] font-semibold text-[#d97706] block mt-0.5">
            {dueCount}
          </span>
          <span className="text-[10px] text-[#76777d] mt-0.5 block">Pending nudge dispatch</span>
        </div>

        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Fulfilled</span>
          <span className="font-mono text-[18px] font-semibold text-[#009668] block mt-0.5">
            {fulfilledCount}
          </span>
          <span className="text-[10px] text-[#009668] font-semibold mt-0.5 block">Successfully settled</span>
        </div>

        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Overdue / Broken</span>
          <span className="font-mono text-[18px] font-semibold text-[#ba1a1a] block mt-0.5">
            {overdueCount}
          </span>
          <span className="text-[10px] text-[#76777d] mt-0.5 block">Requires re-engagement</span>
        </div>

        <div className="bg-white border border-[#e2e8f0] rounded p-3 shadow-2xs">
          <span className="data-label text-[10px] block">Expected Recovery</span>
          <span className="font-mono text-[18px] font-semibold text-[#0b1c30] block mt-0.5">
            {formatINR(totalExpectedAmount)}
          </span>
          <span className="text-[10px] text-[#76777d] mt-0.5 block">Net pipeline value</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="border border-[#e2e8f0] bg-white rounded p-2 flex flex-wrap items-center gap-2 shadow-2xs">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="w-3.5 h-3.5 text-[#76777d] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search payment ID or customer note..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-7 pl-8 pr-3 bg-[#f8f9ff] border border-[#e2e8f0] rounded text-[12px] placeholder:text-[#76777d] focus:border-[#712ae2] focus:ring-1 focus:ring-[#712ae2] outline-none transition"
          />
        </div>

        <div className="flex flex-wrap items-center gap-1">
          {["ALL", "PROMISE_TO_PAY", "FOLLOW_UP_DUE", "FULFILLED", "OVERDUE"].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-2.5 py-0.5 rounded text-[11px] font-medium transition ${
                statusFilter === status
                  ? "bg-[#0b1c30] text-white font-semibold"
                  : "text-[#45464d] hover:text-[#0b1c30] hover:bg-[#f8f9ff]"
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Promises Table */}
      <div className="bg-white border border-[#e2e8f0] rounded shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px] border-collapse whitespace-nowrap">
            <thead>
              <tr className="bg-[#f8f9ff] border-b border-[#e2e8f0] h-[30px] font-label-md text-[11px] text-[#76777d] uppercase tracking-wider font-semibold">
                <th className="px-4 py-1">Customer</th>
                <th className="px-4 py-1">Payment ID</th>
                <th className="px-4 py-1">Amount</th>
                <th className="px-4 py-1">Promise Date</th>
                <th className="px-4 py-1">Status</th>
                <th className="px-4 py-1">Language</th>
                <th className="px-4 py-1">Next Follow-up</th>
                <th className="px-4 py-1">Customer Commitment</th>
                <th className="px-4 py-1 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e2e8f0]/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-[#76777d]">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-6 h-6 rounded-full border-2 border-[#712ae2] border-t-transparent animate-spin" />
                      <span className="text-xs font-medium">Loading commitments...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredPromises.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-[#76777d] text-xs">
                    No promise commitments found matching criteria.
                  </td>
                </tr>
              ) : (
                filteredPromises.map((promise) => {
                  const isExpanded = expandedId === promise.id;
                  return (
                    <React.Fragment key={promise.id}>
                      <tr
                        onClick={() => setExpandedId(isExpanded ? null : promise.id)}
                        className="h-[32px] hover:bg-[#f8f9ff] transition cursor-pointer group"
                      >
                        {/* Customer */}
                        <td className="px-4 font-medium text-[#0b1c30]">
                          Direct Customer
                        </td>

                        {/* Payment ID */}
                        <td className="px-4 font-mono font-semibold text-[#0b1c30] group-hover:text-[#712ae2]">
                          <Link
                            href={`/payments/${promise.payment_id}`}
                            onClick={(e) => e.stopPropagation()}
                          >
                            pay_{promise.payment_id.substring(0, 10)}
                          </Link>
                        </td>

                        {/* Amount */}
                        <td className="px-4 font-mono font-bold text-[#0b1c30]">
                          {formatINR(promise.amount)}
                        </td>

                        {/* Promise Date */}
                        <td className="px-4 font-mono text-[#0b1c30]">
                          {formatDate(promise.promised_date)}
                        </td>

                        {/* Status */}
                        <td className="px-4">
                          {getStatusBadge(promise.status)}
                        </td>

                        {/* Language */}
                        <td className="px-4">
                          <span className="font-mono text-[10px] font-semibold px-1.5 py-0.2 rounded bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe]">
                            {promise.language || "Hinglish"}
                          </span>
                        </td>

                        {/* Next Follow-up */}
                        <td className="px-4 text-[#76777d] font-mono text-[11px]">
                          {promise.follow_up_at ? formatDate(promise.follow_up_at) : "Automated Nudge"}
                        </td>

                        {/* Message Note */}
                        <td className="px-4 text-[#45464d] truncate max-w-xs" title={promise.message}>
                          {promise.message}
                        </td>

                        {/* Actions */}
                        <td className="px-4 text-right">
                          <div className="inline-flex items-center gap-1.5">
                            {promise.status !== "FULFILLED" && promise.status !== "BROKEN" ? (
                              <>
                                <button
                                  onClick={(e) => handleStatusChange(e, promise.id, "FULFILLED")}
                                  className="px-2 py-0.5 rounded bg-[#0b1c30] hover:bg-[#131b2e] text-white text-[11px] font-semibold transition flex items-center gap-0.5 shadow-2xs"
                                >
                                  <Check className="w-3 h-3 text-[#009668]" /> Fulfill
                                </button>
                                <button
                                  onClick={(e) => handleStatusChange(e, promise.id, "BROKEN")}
                                  className="px-2 py-0.5 rounded bg-white hover:bg-rose-50 text-[#ba1a1a] border border-rose-200 text-[11px] font-semibold transition"
                                >
                                  Broken
                                </button>
                              </>
                            ) : (
                              <span className="text-[11px] text-[#76777d] italic">Settled</span>
                            )}
                            <button className="text-[#76777d] hover:text-[#0b1c30] p-0.5">
                              {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Expandable Inspection Drawer */}
                      {isExpanded && (
                        <tr className="bg-[#f8f9ff]/70 border-b border-[#e2e8f0]">
                          <td colSpan={9} className="p-4">
                            <div className="bg-white border border-[#e2e8f0] rounded p-3.5 space-y-3 text-xs">
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                <div>
                                  <span className="data-label text-[10px] block">Customer Context</span>
                                  <span className="font-semibold text-[#0b1c30] block mt-0.5">
                                    Direct Customer (D2C) • ID: {promise.customer_id || "cust_default"}
                                  </span>
                                  <span className="text-[11px] text-[#76777d] block mt-0.5">
                                    Preferred Channel: WhatsApp • Language: {promise.language} ({promise.script || "Latin"})
                                  </span>
                                </div>

                                <div>
                                  <span className="data-label text-[10px] block">Commitment History</span>
                                  <span className="font-mono text-[#0b1c30] block mt-0.5">
                                    Promised Date: {formatDate(promise.promised_date)}
                                  </span>
                                  <span className="font-mono text-[#009668] font-bold block mt-0.5">
                                    Amount Due: {formatINR(promise.amount)}
                                  </span>
                                </div>

                                <div>
                                  <span className="data-label text-[10px] block">Scheduled Action</span>
                                  <span className="font-semibold text-[#712ae2] block mt-0.5">
                                    Smart Retry Window + Payment Link
                                  </span>
                                  <span className="text-[11px] text-[#76777d] block mt-0.5">
                                    Status: {promise.status}
                                  </span>
                                </div>
                              </div>

                              <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0] space-y-1">
                                <span className="data-label text-[10px] block">Customer Communication Fragment</span>
                                <p className="italic text-[#0b1c30] text-[12px] leading-relaxed">
                                  &quot;{promise.message}&quot;
                                </p>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

