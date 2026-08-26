"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchReviewQueue, submitReviewAction } from "@/lib/api";
import { ReviewQueueItem } from "@/lib/types";
import { formatINR, formatDate } from "@/lib/utils";
import {
  UserCheck,
  CheckCircle2,
  XCircle,
  Edit3,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Check,
  X,
  Sparkles,
  ChevronRight,
  Filter,
  Search,
} from "lucide-react";

export default function ReviewPage() {
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(null);
  const [modalType, setModalType] = useState<"APPROVE" | "MODIFY" | "REJECT" | null>(null);
  const [reasonText, setReasonText] = useState("");
  const [modifiedAction, setModifiedAction] = useState("CONTACT_WHATSAPP");
  const [submitting, setSubmitting] = useState(false);
  const [priorityFilter, setPriorityFilter] = useState("ALL");

  const loadQueue = () => {
    setLoading(true);
    fetchReviewQueue()
      .then((data) => {
        setQueue(data);
        if (data.length > 0 && !selectedItem) {
          setSelectedItem(data[0]);
        }
      })
      .catch((err) => console.error("Error loading review queue:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const openActionModal = (
    item: ReviewQueueItem,
    type: "APPROVE" | "MODIFY" | "REJECT"
  ) => {
    setSelectedItem(item);
    setModalType(type);
    setReasonText(
      type === "APPROVE"
        ? "Approved by operator after reviewing customer cohort and transient failure indicators."
        : type === "MODIFY"
        ? "Modified recovery strategy to conversational WhatsApp nudge."
        : "Rejected recovery to prevent customer friction."
    );
  };

  const handleConfirmAction = async () => {
    if (!selectedItem || !modalType) return;
    try {
      setSubmitting(true);
      await submitReviewAction(selectedItem.payment_id, {
        action: modalType,
        modified_action: modalType === "MODIFY" ? modifiedAction : undefined,
        reason: reasonText,
        review_duration_seconds: 14.5,
      });
      setModalType(null);
      loadQueue();
    } catch (err) {
      console.error("Error submitting review action:", err);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredQueue = queue.filter((item) => {
    if (priorityFilter === "HIGH_VALUE") return item.amount >= 20000;
    if (priorityFilter === "CONTRADICTORY") return item.risk_flags.length > 0;
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-[#e2e8f0] pb-3">
        <div>
          <h1 className="font-display text-[22px] font-semibold text-[#0b1c30] tracking-tight">
            Review Queue
          </h1>
          <p className="font-body-md text-[13px] text-[#45464d] mt-0.5">
            Human-in-the-loop operational console for assisted and policy-escalated transactions
          </p>
        </div>

        {/* Priority Filters */}
        <div className="flex items-center gap-1 bg-white p-1 rounded border border-[#e2e8f0] shadow-2xs text-xs font-semibold">
          {[
            { k: "ALL", l: `All (${queue.length})` },
            { k: "HIGH_VALUE", l: "High Value" },
            { k: "CONTRADICTORY", l: "Risk Flags" },
          ].map((f) => (
            <button
              key={f.k}
              onClick={() => setPriorityFilter(f.k)}
              className={`px-2.5 py-0.5 rounded text-[11px] font-medium transition ${
                priorityFilter === f.k
                  ? "bg-[#0b1c30] text-white font-semibold"
                  : "text-[#45464d] hover:text-[#0b1c30] hover:bg-[#f8f9ff]"
              }`}
            >
              {f.l}
            </button>
          ))}
        </div>
      </div>

      {/* Review Layout: Table & Side Inspection Panel */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-2">
            <div className="w-6 h-6 rounded-full border-2 border-[#712ae2] border-t-transparent animate-spin" />
            <span className="text-xs text-[#45464d] font-medium">Loading review queue...</span>
          </div>
        </div>
      ) : queue.length === 0 ? (
        <div className="rounded bg-white border border-[#e2e8f0] p-12 text-center shadow-2xs">
          <CheckCircle2 className="w-8 h-8 text-[#009668] mx-auto mb-2" />
          <h2 className="text-xs font-bold text-[#0b1c30]">Review Queue is Clear</h2>
          <p className="text-xs text-[#45464d] mt-0.5">
            All assisted and escalated transactions have been authorized or reviewed.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
          {/* Left: Queue Table (7 Cols) */}
          <div className="lg:col-span-7 rounded bg-white border border-[#e2e8f0] shadow-2xs overflow-hidden">
            <div className="px-3.5 py-2.5 bg-[#f8f9ff] border-b border-[#e2e8f0] flex items-center justify-between">
              <span className="font-label-md text-[11px] font-bold text-[#0b1c30] uppercase tracking-wider">
                Pending Transactions ({filteredQueue.length})
              </span>
              <span className="text-[11px] text-[#76777d]">Click to inspect</span>
            </div>

            <div className="divide-y divide-[#e2e8f0]/60">
              {filteredQueue.map((item) => {
                const isSelected = selectedItem?.payment_id === item.payment_id;
                return (
                  <div
                    key={item.payment_id}
                    onClick={() => setSelectedItem(item)}
                    className={`p-3.5 cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-[#eff4ff] border-l-2 border-[#712ae2]"
                        : "hover:bg-[#f8f9ff]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-bold text-[#0b1c30] text-xs">
                            {item.order_id}
                          </span>
                          <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#fffbeb] text-[#d97706] border border-[#fde68a]">
                            {item.autonomy_level}
                          </span>
                          <span className="font-mono text-[10px] font-bold text-[#ba1a1a]">
                            {item.policy_decision}
                          </span>
                        </div>
                        <p className="text-xs text-[#0b1c30] font-medium mt-1">
                          {item.customer_name} • <span className="font-mono text-[#475569]">{item.payment_method}</span>
                        </p>
                        <p className="text-[11px] text-[#45464d] truncate max-w-sm mt-0.5">
                          {item.ai_diagnosis}
                        </p>
                      </div>

                      <div className="text-right shrink-0">
                        <div className="font-bold text-[#0b1c30] font-mono text-xs">
                          {formatINR(item.amount)}
                        </div>
                        <div className="text-[10px] font-mono mt-0.5 flex items-center justify-end gap-1 text-[#712ae2] font-semibold">
                          <Sparkles className="w-3 h-3" />
                          <span>{(item.ai_confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Inspection & Decision Panel (5 Cols) */}
          {selectedItem && (
            <div className="lg:col-span-5 rounded bg-white border border-[#e2e8f0] p-4 shadow-2xs space-y-3 sticky top-16">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] pb-2.5">
                <div>
                  <span className="data-label text-[10px] block">Selected Payment</span>
                  <h2 className="text-xs font-bold text-[#0b1c30] font-mono">
                    {selectedItem.order_id}
                  </h2>
                </div>
                <div className="text-right">
                  <span className="data-label text-[10px] block">Amount</span>
                  <span className="text-base font-black text-[#0b1c30] font-mono">
                    {formatINR(selectedItem.amount)}
                  </span>
                </div>
              </div>

              {/* AI Diagnostic Summary */}
              <div className="p-3 bg-[#f8f9ff] rounded border border-[#e2e8f0] space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1 font-bold text-[#712ae2] text-xs">
                    <Sparkles className="w-3.5 h-3.5 text-[#712ae2]" />
                    AI Diagnostic Analysis
                  </div>
                  <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe]">
                    Conf: {(selectedItem.ai_confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="font-semibold text-[#0b1c30] mt-0.5">{selectedItem.ai_diagnosis}</p>
                <div className="text-[11px] text-[#45464d] space-y-0.5 mt-1">
                  <div>
                    Recommended Action: <strong className="text-[#0b1c30] font-mono">{selectedItem.ai_recommended_action}</strong>
                  </div>
                  <div>Rationale: {selectedItem.ai_rationale}</div>
                </div>
              </div>

              {/* Policy Rules & Risk Flags */}
              <div className="space-y-1 text-xs">
                <span className="data-label text-[10px] block">Policy Checklist:</span>
                <div className="space-y-1">
                  {selectedItem.policy_reasons.map((r, i) => (
                    <div key={i} className="flex items-start gap-1.5 text-[#45464d] text-[11px]">
                      <span className="text-[#d97706] font-bold">•</span>
                      <span>{r}</span>
                    </div>
                  ))}
                  {selectedItem.risk_flags.length > 0 && (
                    <div className="pt-1 flex flex-wrap gap-1">
                      {selectedItem.risk_flags.map((flag, idx) => (
                        <span
                          key={idx}
                          className="px-1.5 py-0.2 rounded bg-[#fff1f2] text-[#ba1a1a] text-[10px] font-mono border border-[#fecdd3] font-semibold"
                        >
                          ⚠️ {flag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 border-t border-[#f1f5f9] space-y-2">
                <div className="grid grid-cols-3 gap-1.5">
                  <button
                    onClick={() => openActionModal(selectedItem, "APPROVE")}
                    className="py-1.5 px-2 rounded bg-[#0b1c30] hover:bg-[#131b2e] text-white text-xs font-semibold shadow-2xs transition flex items-center justify-center gap-1"
                  >
                    <Check className="w-3.5 h-3.5 text-[#009668]" /> Approve
                  </button>
                  <button
                    onClick={() => openActionModal(selectedItem, "MODIFY")}
                    className="py-1.5 px-2 rounded bg-white hover:bg-[#f8f9ff] text-[#0b1c30] border border-[#e2e8f0] text-xs font-semibold shadow-2xs transition flex items-center justify-center gap-1"
                  >
                    <Edit3 className="w-3.5 h-3.5" /> Modify
                  </button>
                  <button
                    onClick={() => openActionModal(selectedItem, "REJECT")}
                    className="py-1.5 px-2 rounded bg-white hover:bg-rose-50 text-[#ba1a1a] border border-rose-200 text-xs font-semibold shadow-2xs transition flex items-center justify-center gap-1"
                  >
                    <X className="w-3.5 h-3.5" /> Reject
                  </button>
                </div>

                <Link
                  href={`/payments/${selectedItem.payment_id}`}
                  className="w-full flex items-center justify-center gap-1 py-1 text-xs text-[#712ae2] hover:underline font-semibold"
                >
                  <span>Inspect Full Payment Journey</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action Modal */}
      {modalType && selectedItem && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="rounded bg-white border border-[#e2e8f0] p-5 max-w-md w-full shadow-modal space-y-3">
            <div className="flex items-center justify-between border-b border-[#f1f5f9] pb-2">
              <h3 className="text-xs font-bold text-[#0b1c30] uppercase">
                {modalType === "APPROVE" && "Approve Recovery Action"}
                {modalType === "MODIFY" && "Modify Recovery Strategy"}
                {modalType === "REJECT" && "Reject & Terminate Recovery"}
              </h3>
              <button
                onClick={() => setModalType(null)}
                className="p-1 rounded text-[#76777d] hover:text-[#0b1c30]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-[#45464d]">
              Payment: <strong className="text-[#0b1c30] font-mono">{selectedItem.order_id}</strong> (
              {formatINR(selectedItem.amount)})
            </p>

            {modalType === "MODIFY" && (
              <div className="space-y-1">
                <label className="data-label text-[10px] block">Select New Strategy</label>
                <select
                  value={modifiedAction}
                  onChange={(e) => setModifiedAction(e.target.value)}
                  className="w-full bg-[#f8f9ff] border border-[#e2e8f0] rounded p-1.5 text-xs text-[#0b1c30] font-medium outline-none focus:ring-1 focus:ring-[#712ae2]"
                >
                  <option value="CONTACT_WHATSAPP">Send WhatsApp Recovery Link</option>
                  <option value="SEND_PAYMENT_LINK">Issue Dynamic UPI Payment Link</option>
                  <option value="RETRY_SMART_SCHEDULE">Schedule Retry in +24h</option>
                  <option value="RETRY_NOW">Execute Immediate Retry</option>
                </select>
              </div>
            )}

            <div className="space-y-1">
              <label className="data-label text-[10px] block">Reviewer Rationale</label>
              <textarea
                value={reasonText}
                onChange={(e) => setReasonText(e.target.value)}
                rows={3}
                className="w-full bg-[#f8f9ff] border border-[#e2e8f0] rounded p-2 text-xs text-[#0b1c30] placeholder-[#76777d] outline-none focus:ring-1 focus:ring-[#712ae2]"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#f1f5f9]">
              <button
                onClick={() => setModalType(null)}
                disabled={submitting}
                className="px-2.5 py-1 rounded bg-white hover:bg-[#f1f5f9] border border-[#e2e8f0] text-[#0b1c30] text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmAction}
                disabled={submitting}
                className="px-3 py-1 rounded bg-[#0b1c30] hover:bg-[#131b2e] text-white text-xs font-bold disabled:opacity-50 flex items-center gap-1 shadow-2xs"
              >
                {submitting ? "Processing..." : "Confirm Decision"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

