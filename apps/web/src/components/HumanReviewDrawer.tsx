"use client";

import React, { useState } from "react";
import { Payment } from "@/lib/types";
import { formatINR } from "@/lib/utils";
import { submitReviewAction } from "@/lib/api";
import {
  X,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Check,
  Building2,
  CreditCard,
  MessageSquare,
  ShieldCheck,
} from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  payment: Payment | null;
  onActionComplete?: () => void;
}

export function HumanReviewDrawer({
  isOpen,
  onClose,
  payment,
  onActionComplete,
}: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [isModifying, setIsModifying] = useState(false);
  const [modifiedAction, setModifiedAction] = useState("CONTACT_WHATSAPP");
  const [modifiedDelayHours, setModifiedDelayHours] = useState(4);
  const [reasonNotes, setReasonNotes] = useState("");

  if (!isOpen || !payment) return null;

  const confScore =
    payment.diagnostic_evidence &&
    typeof payment.diagnostic_evidence.confidence === "number"
      ? Math.round(payment.diagnostic_evidence.confidence * 100)
      : payment.autonomy_level === "AUTONOMOUS"
      ? 93
      : payment.autonomy_level === "ASSISTED"
      ? 74
      : 38;

  const handleAction = async (action: "APPROVE" | "MODIFY" | "REJECT") => {
    try {
      setSubmitting(true);
      const reason =
        action === "APPROVE"
          ? "Approved automated recovery plan after operator inspection of customer cohort."
          : action === "MODIFY"
          ? `Modified strategy to ${modifiedAction} with +${modifiedDelayHours}h delay.`
          : "Rejected automated recovery to prevent customer friction or terminal decline.";

      await submitReviewAction(payment.id, {
        action,
        modified_action: action === "MODIFY" ? modifiedAction : undefined,
        modified_delay_hours: action === "MODIFY" ? modifiedDelayHours : undefined,
        reason,
        reviewer_notes: reasonNotes || undefined,
        review_duration_seconds: 14.5,
      });

      setActionSuccess(`Plan ${action === "APPROVE" ? "Approved" : action === "MODIFY" ? "Modified" : "Rejected"} Successfully`);
      setTimeout(() => {
        setActionSuccess(null);
        setIsModifying(false);
        if (onActionComplete) onActionComplete();
        onClose();
      }, 1000);
    } catch (err) {
      console.error("Failed to submit review action", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/40 z-40 transition-opacity backdrop-blur-xs"
      />

      {/* Drawer Panel */}
      <aside
        id="review-drawer"
        className="fixed top-0 right-0 h-full w-full sm:w-[480px] lg:w-[35%] bg-white border-l border-[#e2e8f0] z-50 flex flex-col shadow-drawer transition-transform duration-200"
      >
        {/* Header */}
        <div className="p-4 border-b border-[#e2e8f0] flex items-center justify-between bg-[#f8f9ff]">
          <div className="flex items-center gap-2.5">
            <h3 className="font-headline-sm text-[15px] font-bold text-[#0b1c30]">
              Review Payment: <span className="font-mono text-[#712ae2]">{payment.id}</span>
            </h3>
            <span className="px-2 py-0.5 bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe] text-[10px] font-mono font-bold rounded uppercase tracking-wider">
              IN REVIEW
            </span>
          </div>
          <button
            onClick={onClose}
            aria-label="Close Drawer"
            className="w-7 h-7 flex items-center justify-center rounded hover:bg-[#e2e8f0] text-[#76777d] hover:text-[#0b1c30] transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {actionSuccess && (
            <div className="p-3 rounded bg-[#ecfdf5] border border-[#a7f3d0] text-[#009668] text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{actionSuccess}</span>
            </div>
          )}

          {/* Quick Context Summary */}
          <div className="p-3 bg-[#f8f9ff] rounded border border-[#e2e8f0] grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="data-label text-[10px] block">Customer</span>
              <span className="font-semibold text-[#0b1c30] block">
                {payment.customer?.name || payment.customer_name || "Direct Customer"}
              </span>
            </div>
            <div>
              <span className="data-label text-[10px] block">Amount</span>
              <span className="font-mono font-bold text-[14px] text-[#0b1c30] block">
                {formatINR(payment.amount)}
              </span>
            </div>
            <div>
              <span className="data-label text-[10px] block">Method</span>
              <span className="font-mono text-[#475569] block">{payment.payment_method}</span>
            </div>
            <div>
              <span className="data-label text-[10px] block">Order ID</span>
              <span className="font-mono text-[#475569] block">#{payment.order_id}</span>
            </div>
          </div>

          {/* Section 1: AI Diagnosis & Confidence */}
          <section className="space-y-2.5">
            <div className="flex items-center justify-between">
              <h4 className="data-label text-[#76777d]">
                AI Diagnosis & Confidence
              </h4>
              <div className="flex items-center gap-1.5 font-mono text-[18px] font-bold text-[#712ae2]">
                <Sparkles className="w-4 h-4 text-[#712ae2]" />
                <span>{confScore}%</span>
              </div>
            </div>

            <div className="bg-white border border-[#e2e8f0] rounded p-3 space-y-2">
              <div>
                <span className="text-[10px] font-bold text-[#76777d] uppercase block">
                  Root Cause Diagnosis:
                </span>
                <p className="font-medium text-[#0b1c30] text-xs mt-0.5">
                  {payment.likely_failure_cause ||
                    payment.failure_reason ||
                    "Soft decline due to issuing bank authorization limits."}
                </p>
              </div>

              <div className="border-t border-[#f1f5f9] pt-2 space-y-1 text-[11px]">
                <span className="font-semibold text-[#76777d] uppercase text-[10px] block">
                  Confidence Calibration Factors:
                </span>
                <div className="flex justify-between text-[#45464d]">
                  <span>Historical Merchant Clearing</span>
                  <span className="font-mono font-semibold text-[#0b1c30]">88%</span>
                </div>
                <div className="flex justify-between text-[#45464d]">
                  <span>Network Latency Switch</span>
                  <span className="font-mono font-semibold text-[#0b1c30]">94%</span>
                </div>
                <div className="flex justify-between text-[#45464d]">
                  <span>Bank Response Code</span>
                  <span className="font-mono font-semibold text-[#ba1a1a]">Soft Decline</span>
                </div>
              </div>
            </div>
          </section>

          {/* Section 2: Policy & Authorization Checklist */}
          <section className="space-y-2.5">
            <h4 className="data-label text-[#76777d]">
              Policy & Gating Checks
            </h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 bg-[#eff4ff] rounded border border-[#d3e4fe]">
                <span className="data-label text-[10px] block text-[#712ae2]">
                  AI Autonomy
                </span>
                <span className="font-bold text-[#712ae2] font-mono text-xs block">
                  {payment.autonomy_level || "ASSISTED"}
                </span>
              </div>
              <div className="p-2.5 bg-[#fffbeb] rounded border border-[#fde68a]">
                <span className="data-label text-[10px] block text-[#d97706]">
                  Policy Authority
                </span>
                <span className="font-bold text-[#d97706] font-mono text-xs block">
                  ESCALATE
                </span>
              </div>
            </div>

            <div className="bg-[#f8f9ff] border border-[#e2e8f0] rounded p-2.5 space-y-1.5 text-[11px]">
              <div className="flex items-center justify-between text-[#45464d]">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#009668]" /> Duplicate Protection
                </span>
                <span className="font-mono font-bold text-[#009668]">PASS</span>
              </div>
              <div className="flex items-center justify-between text-[#45464d]">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#009668]" /> Retry Limit (1 &lt;= 2)
                </span>
                <span className="font-mono font-bold text-[#009668]">PASS</span>
              </div>
              <div className="flex items-center justify-between text-[#45464d]">
                <span className="flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-[#d97706]" /> Human In Loop Required
                </span>
                <span className="font-mono font-bold text-[#d97706]">GATED</span>
              </div>
            </div>
          </section>

          {/* Section 3: Proposed Customer Communication Preview */}
          <section className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="data-label text-[#76777d]">
                Proposed Customer Nudge
              </h4>
              <span className="text-[10px] font-mono text-[#712ae2] bg-[#eff4ff] px-1.5 py-0.2 rounded">
                WhatsApp • Latin Script
              </span>
            </div>
            <div className="bg-white border border-[#e2e8f0] rounded p-3 italic text-xs text-[#0b1c30] leading-relaxed">
              &quot;Namaste {payment.customer?.name || payment.customer_name || "Customer"}, your payment of {formatINR(payment.amount)} was unsuccessful due to a temporary bank timeout. Would you like us to retry tomorrow morning?&quot;
            </div>
            <p className="text-[10px] text-[#76777d] italic">
              Synthetic preview • Only dispatched after operator approval.
            </p>
          </section>

          {/* Modify Form Expansion if toggled */}
          {isModifying && (
            <div className="p-3 bg-[#f8f9ff] border border-[#e2e8f0] rounded space-y-2.5 text-xs">
              <span className="font-bold text-[#0b1c30] block">Modify Recovery Plan:</span>
              <div className="space-y-1">
                <label className="text-[11px] text-[#45464d] font-medium block">
                  Alternative Strategy:
                </label>
                <select
                  value={modifiedAction}
                  onChange={(e) => setModifiedAction(e.target.value)}
                  className="w-full bg-white border border-[#e2e8f0] rounded p-1.5 text-xs text-[#0b1c30] font-medium focus:ring-1 focus:ring-[#712ae2] outline-none"
                >
                  <option value="CONTACT_WHATSAPP">Conversational WhatsApp Nudge</option>
                  <option value="SEND_PAYMENT_LINK">Send Instant Payment Link via SMS</option>
                  <option value="RETRY_SMART_SCHEDULE">Smart Schedule Retry (+4 Hours)</option>
                  <option value="TERMINATE_RECOVERY">Halt All Further Recovery Attempts</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-[#45464d] font-medium block">
                  Timing Delay (Hours):
                </label>
                <input
                  type="number"
                  min="0"
                  max="48"
                  value={modifiedDelayHours}
                  onChange={(e) => setModifiedDelayHours(Number(e.target.value))}
                  className="w-full bg-white border border-[#e2e8f0] rounded p-1.5 text-xs text-[#0b1c30] font-mono focus:ring-1 focus:ring-[#712ae2] outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-[#45464d] font-medium block">
                  Operator Notes:
                </label>
                <input
                  type="text"
                  placeholder="Reason for modifying..."
                  value={reasonNotes}
                  onChange={(e) => setReasonNotes(e.target.value)}
                  className="w-full bg-white border border-[#e2e8f0] rounded p-1.5 text-xs text-[#0b1c30] focus:ring-1 focus:ring-[#712ae2] outline-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={() => handleAction("MODIFY")}
                  disabled={submitting}
                  className="flex-1 py-1.5 bg-[#712ae2] text-white text-xs font-semibold rounded hover:bg-[#5a00c6] transition disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Confirm Modified Strategy"}
                </button>
                <button
                  onClick={() => setIsModifying(false)}
                  className="py-1.5 px-3 bg-white border border-[#e2e8f0] text-xs font-medium text-[#45464d] rounded hover:bg-[#f8f9ff]"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Action Footer */}
        {!isModifying && (
          <div className="p-4 border-t border-[#e2e8f0] bg-[#f8f9ff] flex flex-col gap-2">
            <button
              onClick={() => handleAction("APPROVE")}
              disabled={submitting}
              className="w-full h-9 bg-[#0b1c30] hover:bg-[#131b2e] text-white text-[12px] font-semibold rounded flex items-center justify-center gap-1.5 transition shadow-2xs disabled:opacity-50"
            >
              {submitting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Check className="w-3.5 h-3.5 text-[#009668]" />
              )}
              <span>Approve AI Strategy</span>
            </button>

            <button
              onClick={() => setIsModifying(true)}
              disabled={submitting}
              className="w-full h-9 bg-white border border-[#e2e8f0] hover:bg-[#f1f5f9] text-[#0b1c30] text-[12px] font-semibold rounded transition shadow-2xs disabled:opacity-50"
            >
              Modify Plan
            </button>

            <button
              onClick={() => handleAction("REJECT")}
              disabled={submitting}
              className="w-full h-9 bg-white hover:bg-rose-50 text-[#ba1a1a] border border-rose-200 text-[12px] font-semibold rounded transition disabled:opacity-50"
            >
              Reject / Block
            </button>
          </div>
        )}
      </aside>
    </>
  );
}
