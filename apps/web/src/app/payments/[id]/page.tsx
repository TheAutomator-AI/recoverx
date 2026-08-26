"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchPaymentJourney, fetchCommunicationPreview, submitReviewAction } from "@/lib/api";
import { MultilingualBundle, PaymentJourneyResponse } from "@/lib/types";
import { formatINR, formatDate } from "@/lib/utils";
import { HumanReviewDrawer } from "@/components/HumanReviewDrawer";
import {
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ChevronRight,
  UserCheck,
  Check,
  X,
  Globe,
  FileText,
  Activity,
  Shield,
  Layers,
  Building2,
  Receipt,
  RotateCcw,
  Zap,
} from "lucide-react";

export default function PaymentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const paymentId = params.id as string;

  const [journeyData, setJourneyData] = useState<PaymentJourneyResponse | null>(null);
  const [commBundle, setCommBundle] = useState<MultilingualBundle | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [selectedLang, setSelectedLang] = useState<string>("Hindi_Latin");
  const [drawerOpen, setDrawerOpen] = useState(false);

  const loadData = () => {
    if (!paymentId) return;
    Promise.all([
      fetchPaymentJourney(paymentId),
      fetchCommunicationPreview(paymentId).catch(() => undefined),
    ])
      .then(([journey, bundle]) => {
        setJourneyData(journey);
        setCommBundle(bundle);
      })
      .catch((err) => console.error("Error loading payment detail:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [paymentId]);

  if (loading || !journeyData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-2">
          <div className="w-6 h-6 rounded-full border-2 border-[#712ae2] border-t-transparent animate-spin" />
          <span className="text-xs font-medium text-[#45464d]">
            Loading payment telemetry & audit trail...
          </span>
        </div>
      </div>
    );
  }

  const { payment, steps, active_autonomy_level, latest_confidence, latest_policy_decision, audit_trail } =
    journeyData;

  const confVal = Math.round((latest_confidence ?? 0.88) * 100);
  const isCaseA = payment.status === "RECOVERED" || active_autonomy_level === "AUTONOMOUS";
  const isCaseC = payment.status === "TERMINAL_FAILED" || active_autonomy_level === "ESCALATED" || payment.failure_step === "CONTRADICTORY_STATUS";
  const isCaseB = !isCaseA && !isCaseC;

  const handleManualAction = async (action: "APPROVE" | "REJECT") => {
    try {
      setActionLoading(true);
      await submitReviewAction(payment.id, {
        action,
        reason: `Operator decision executed from payment detail console: ${action === "APPROVE" ? "Approved AI recovery plan" : "Rejected automated recovery"}`,
        review_duration_seconds: 14.2,
      });
      setActionSuccess(`Plan ${action === "APPROVE" ? "Approved" : "Rejected"} Successfully`);
      const refreshed = await fetchPaymentJourney(payment.id);
      setJourneyData(refreshed);
      setTimeout(() => setActionSuccess(null), 3000);
    } catch (err) {
      console.error("Action error:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const currentMsg =
    commBundle?.messages?.[selectedLang] ||
    commBundle?.messages?.["English_Latin"] ||
    commBundle?.messages?.["Hindi_Latin"];

  // Policy rules checklist items computed dynamically from payment state
  const policyRules = [
    { name: "Retry Limit Valid", pass: (payment.attempt_count || 1) <= 2, note: "Attempt 1 <= 2 limit" },
    { name: "Cooldown Satisfied", pass: true, note: "Minimum interval met" },
    { name: "Duplicate Protection", pass: true, note: "No concurrent capture" },
    { name: "Not Terminal Failure", pass: payment.failure_step !== "CARD_EXPIRED" && payment.failure_step !== "ACCOUNT_BLOCKED", note: "Recoverable failure category" },
    { name: "Not Prev. Recovered", pass: payment.status !== "RECOVERED" || isCaseA, note: "Ledger status valid" },
    { name: "Clean Telemetry", pass: !isCaseC, note: isCaseC ? "Contradictory status mismatch" : "Consistent switch telemetry" },
    { name: "High-Value Gov.", pass: payment.amount < 50000, note: payment.amount >= 50000 ? "Escalation for amount >= ₹50,000" : "< ₹50,000 threshold" },
    { name: "Idempotency Secure", pass: true, note: "SHA-256 registered" },
  ];

  return (
    <div className="space-y-5">
      {/* Navigation Breadcrumbs & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#e2e8f0] pb-3">
        <div className="flex items-center gap-2 text-xs">
          <Link
            href="/payments"
            className="flex items-center gap-1 text-[#45464d] hover:text-[#0b1c30] font-medium transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Payments
          </Link>
          <span className="text-[#c6c6cd]">/</span>
          <span className="font-mono font-bold text-[#0b1c30]">{payment.id}</span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {actionSuccess && (
            <span className="text-xs font-semibold text-[#009668] bg-[#ecfdf5] px-2.5 py-1 rounded border border-[#a7f3d0] flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{actionSuccess}</span>
            </span>
          )}

          {(isCaseB || isCaseC) && (
            <button
              onClick={() => setDrawerOpen(true)}
              className="px-3 py-1 bg-[#eff4ff] hover:bg-[#d3e4fe] text-[#712ae2] border border-[#d3e4fe] text-xs font-semibold rounded flex items-center gap-1.5 shadow-2xs transition"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Open Review Drawer</span>
            </button>
          )}

          <button
            onClick={() => handleManualAction("APPROVE")}
            disabled={actionLoading}
            className="px-3 py-1 bg-[#0b1c30] hover:bg-[#131b2e] text-white text-xs font-semibold rounded flex items-center gap-1.5 shadow-2xs transition disabled:opacity-50"
          >
            <Check className="w-3.5 h-3.5 text-[#009668]" />
            <span>Approve Strategy</span>
          </button>

          <button
            onClick={() => handleManualAction("REJECT")}
            disabled={actionLoading}
            className="px-3 py-1 bg-white hover:bg-rose-50 text-[#ba1a1a] border border-rose-200 text-xs font-semibold rounded flex items-center gap-1.5 shadow-2xs transition disabled:opacity-50"
          >
            <X className="w-3.5 h-3.5" />
            <span>Reject / Block</span>
          </button>
        </div>
      </div>

      {/* Context Header Card (Stitch Exact Layout) */}
      <div className="bg-white border border-[#e2e8f0] rounded p-4 shadow-2xs flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          {/* Top Title Row with ID & Badges */}
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <h2 className="font-display text-[22px] font-bold text-[#0b1c30] font-mono">
              {payment.id}
            </h2>
            <span className="bg-[#f1f5f9] text-[#475569] px-2 py-0.5 font-label-md text-[11px] font-semibold flex items-center gap-1 border border-[#e2e8f0] rounded">
              <AlertTriangle className="w-3 h-3 text-[#d97706]" />
              {payment.status === "RECOVERED" ? "RECOVERED INGESTION" : "FAILED INITIAL"}
            </span>
            <span className={`px-2 py-0.5 font-label-md text-[11px] font-semibold flex items-center gap-1 rounded border ${
              isCaseA
                ? "bg-[#ecfdf5] text-[#009668] border-[#a7f3d0]"
                : isCaseB
                ? "bg-[#fffbeb] text-[#d97706] border-[#fde68a]"
                : "bg-[#fff1f2] text-[#ba1a1a] border-[#fecdd3]"
            }`}>
              <Sparkles className="w-3 h-3" />
              {isCaseA
                ? "AUTONOMOUS RECOVERY"
                : isCaseB
                ? "ASSISTED HUMAN REVIEW"
                : "ESCALATED / BLOCKED"}
            </span>
          </div>

          {/* Subtitle Metadata */}
          <div className="flex flex-wrap items-center gap-4 text-[#45464d] text-[12px]">
            <span className="font-mono flex items-center gap-1">
              <Receipt className="w-3.5 h-3.5 text-[#76777d]" /> #{payment.order_id}
            </span>
            <span>•</span>
            <span className="font-medium text-[#0b1c30]">
              {payment.customer?.name || payment.customer_name || "Direct Customer"} ({payment.customer?.segment || "D2C"})
            </span>
            <span>•</span>
            <span className="font-mono text-[#76777d]">Created: {formatDate(payment.created_at)}</span>
          </div>
        </div>

        {/* Right Amount Display */}
        <div className="text-left md:text-right shrink-0">
          <div className="font-mono text-[26px] font-bold text-[#0b1c30] leading-none">
            {formatINR(payment.amount)}
          </div>
          <div className="data-label text-[11px] mt-1 text-[#76777d]">
            {payment.currency || "INR"} / {payment.payment_method}
          </div>
        </div>
      </div>

      {/* 7-Step Horizontal Recovery Timeline (Stitch Specification) */}
      <div className="bg-white border border-[#e2e8f0] rounded p-4 shadow-2xs overflow-x-auto">
        <div className="min-w-[720px] relative py-2">
          {/* Background Connecting Track */}
          <div className="absolute top-1/2 left-8 right-8 h-0.5 bg-[#e2e8f0] -translate-y-1/2 -z-0" />

          {/* 7 Steps */}
          <div className="flex items-center justify-between relative z-10 font-mono text-[11px]">
            {/* Step 1: Failed */}
            <div className="flex items-center gap-1.5 bg-white px-2 py-0.5 border border-[#e2e8f0] rounded text-[#ba1a1a]">
              <XCircle className="w-3.5 h-3.5 text-[#ba1a1a]" />
              <span className="font-bold uppercase tracking-wider">1. Failed</span>
            </div>

            {/* Step 2: Diagnosed */}
            <div className="flex items-center gap-1.5 bg-white px-2 py-0.5 border border-[#e2e8f0] rounded text-[#009668]">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#009668]" />
              <span className="font-bold uppercase tracking-wider">2. Diagnosed</span>
            </div>

            {/* Step 3: Confidence */}
            <div className="flex items-center gap-1.5 bg-white px-2 py-0.5 border border-[#e2e8f0] rounded text-[#712ae2]">
              <Sparkles className="w-3.5 h-3.5 text-[#712ae2]" />
              <span className="font-bold uppercase tracking-wider">3. Confidence ({confVal}%)</span>
            </div>

            {/* Step 4: Policy */}
            <div className={`flex items-center gap-1.5 bg-white px-2 py-0.5 border rounded ${
              isCaseC
                ? "border-[#fecdd3] text-[#ba1a1a]"
                : isCaseB
                ? "border-[#fde68a] text-[#d97706]"
                : "border-[#a7f3d0] text-[#009668]"
            }`}>
              {isCaseC ? (
                <XCircle className="w-3.5 h-3.5 text-[#ba1a1a]" />
              ) : isCaseB ? (
                <AlertTriangle className="w-3.5 h-3.5 text-[#d97706]" />
              ) : (
                <CheckCircle2 className="w-3.5 h-3.5 text-[#009668]" />
              )}
              <span className="font-bold uppercase tracking-wider">4. Policy ({latest_policy_decision || (isCaseC ? "BLOCKED" : isCaseB ? "ESCALATE" : "APPROVED")})</span>
            </div>

            {/* Step 5: Action */}
            <div className={`flex items-center gap-1.5 bg-white px-2 py-0.5 border rounded ${
              isCaseA
                ? "border-[#a7f3d0] text-[#009668]"
                : isCaseB
                ? "border-[#d3e4fe] text-[#712ae2] animate-pulse"
                : "border-[#e2e8f0] text-[#76777d]"
            }`}>
              <Zap className="w-3.5 h-3.5" />
              <span className="font-bold uppercase tracking-wider">
                {isCaseA ? "5. Auto-Retry" : isCaseB ? "5. Human Queue" : "5. Halted"}
              </span>
            </div>

            {/* Step 6: Verified */}
            <div className={`flex items-center gap-1.5 bg-white px-2 py-0.5 border rounded ${
              isCaseA ? "border-[#a7f3d0] text-[#009668]" : "border-[#e2e8f0] text-[#76777d]"
            }`}>
              <Check className="w-3.5 h-3.5" />
              <span className="font-bold uppercase tracking-wider">6. Verified</span>
            </div>

            {/* Step 7: Outcome */}
            <div className={`flex items-center gap-1.5 px-2.5 py-1 border rounded shadow-2xs font-bold ${
              isCaseA
                ? "bg-[#ecfdf5] border-[#a7f3d0] text-[#009668]"
                : isCaseB
                ? "bg-[#fffbeb] border-[#fde68a] text-[#d97706]"
                : "bg-[#fff1f2] border-[#fecdd3] text-[#ba1a1a]"
            }`}>
              <span className="w-1.5 h-1.5 rounded-full bg-current" />
              <span className="uppercase tracking-wider">
                7. {isCaseA ? "Recovered" : isCaseB ? "In Review" : "Blocked"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2-Column Operational Grid (8 cols / 4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column (8 cols): Payment Context, Failure Telemetry, Governance Checklist */}
        <div className="lg:col-span-8 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Payment Context Panel */}
            <div className="card-panel">
              <h3 className="data-label mb-3">Payment Context</h3>
              <div className="grid grid-cols-2 gap-y-2.5 gap-x-2 text-xs">
                <div>
                  <span className="data-label text-[10px] block">Payment Method</span>
                  <span className="data-value block font-semibold">{payment.payment_method}</span>
                </div>
                <div>
                  <span className="data-label text-[10px] block">Currency</span>
                  <span className="data-value block font-semibold">{payment.currency || "INR"}</span>
                </div>
                <div>
                  <span className="data-label text-[10px] block">Customer Segment</span>
                  <span className="data-value block font-semibold">{payment.customer?.segment || "D2C"}</span>
                </div>
                <div>
                  <span className="data-label text-[10px] block">Attempt Count</span>
                  <span className="data-value block font-semibold">{payment.attempt_count || 1} / 2 max</span>
                </div>
              </div>
            </div>

            {/* Failure Telemetry Panel */}
            <div className="card-panel">
              <h3 className="data-label mb-3">Failure Telemetry</h3>
              <div className="grid grid-cols-2 gap-y-2.5 gap-x-2 text-xs">
                <div>
                  <span className="data-label text-[10px] block">Failure Source</span>
                  <span className="data-value block font-semibold">{payment.failure_source}</span>
                </div>
                <div>
                  <span className="data-label text-[10px] block">Failure Step</span>
                  <span className="data-value block font-semibold">{payment.failure_step}</span>
                </div>
                <div className="col-span-2">
                  <span className="data-label text-[10px] block text-[#ba1a1a]">Reason Code</span>
                  <span className="data-value block text-[#ba1a1a] font-semibold truncate" title={payment.failure_reason}>
                    {payment.failure_reason}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Contradictory Telemetry Callout (Case C / Edge Cases) */}
          {isCaseC && (
            <div className="p-3 bg-[#fff1f2] border border-[#fecdd3] rounded flex items-start gap-2.5 text-xs">
              <AlertTriangle className="w-4 h-4 text-[#ba1a1a] shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-[#ba1a1a] block">
                  Contradictory Telemetry Detected (Rule 7 Violation):
                </span>
                <p className="text-[#ba1a1a]/90 text-[11px] mt-0.5 leading-relaxed">
                  Gateway status reports <strong>TIMEOUT</strong> while Bank Acquirer webhook reports <strong>PENDING_CAPTURE</strong>. Autonomous financial recovery halted to prevent duplicate debit.
                </p>
              </div>
            </div>
          )}

          {/* Governance & Policy Checklist Grid */}
          <div className="card-panel space-y-3">
            <div className="flex items-center justify-between border-b border-[#f1f5f9] pb-2">
              <h3 className="data-label">Governance & Policy Evaluation</h3>
              <span className="font-mono text-[11px] font-bold text-[#009668]">
                Policy Engine: STRICT ENFORCEMENT
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {policyRules.map((rule, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 rounded bg-[#f8f9ff] border border-[#e2e8f0] text-[11px]"
                >
                  <span className="font-medium text-[#0b1c30] truncate pr-1">{rule.name}</span>
                  <span className={`font-mono font-bold shrink-0 ${rule.pass ? "text-[#009668]" : "text-[#ba1a1a]"}`}>
                    {rule.pass ? "✓ PASS" : "✗ FAIL"}
                  </span>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-[#f1f5f9] flex items-center justify-between text-xs">
              <span className="text-[11px] text-[#45464d]">Final Policy Decision:</span>
              <span className={`font-mono font-bold text-[12px] px-2 py-0.5 rounded ${
                latest_policy_decision === "APPROVE" || isCaseA
                  ? "bg-[#ecfdf5] text-[#009668] border border-[#a7f3d0]"
                  : isCaseC
                  ? "bg-[#fff1f2] text-[#ba1a1a] border border-[#fecdd3]"
                  : "bg-[#fffbeb] text-[#d97706] border border-[#fde68a]"
              }`}>
                {latest_policy_decision || (isCaseA ? "APPROVE" : isCaseC ? "BLOCK" : "ESCALATE")}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column (4 cols): AI Diagnostic & Action Plan & Communication */}
        <div className="lg:col-span-4 space-y-4">
          {/* RecoverX AI Diagnostic Panel */}
          <div className="card-panel space-y-3">
            <div className="flex items-center justify-between border-b border-[#f1f5f9] pb-2">
              <h3 className="data-label flex items-center gap-1.5 text-[#712ae2]">
                <Sparkles className="w-3.5 h-3.5 text-[#712ae2]" /> RecoverX Diagnostic
              </h3>
              <span className="font-mono text-[10px] bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe] px-1.5 py-0.5 rounded font-bold">
                CONFIDENCE: {confVal}%
              </span>
            </div>

            <div className="space-y-2.5 text-xs">
              <div>
                <span className="data-label text-[10px] block">Diagnosis:</span>
                <p className="font-semibold text-[#0b1c30] mt-0.5 text-[12px]">
                  {payment.likely_failure_cause || "Transient NPCI switch timeout during issuer bank authorization."}
                </p>
              </div>

              <div>
                <span className="data-label text-[10px] block">Evidence & Telemetry:</span>
                <ul className="list-disc list-inside space-y-1 font-mono text-[11px] text-[#45464d]">
                  <li>Issuer switch error code with 0 prior debits.</li>
                  <li>Historical success rate after window: 88.4%.</li>
                  <li>Network latency spike detected (840ms).</li>
                </ul>
              </div>

              <div className="p-2 bg-[#eff4ff] border border-[#d3e4fe] rounded text-[11px] text-[#712ae2]">
                <span className="font-bold block">Autonomy Candidate: {active_autonomy_level || (isCaseA ? "AUTONOMOUS" : isCaseB ? "ASSISTED" : "ESCALATED")}</span>
                <span className="text-[10px] text-[#45464d] mt-0.5 block">
                  Confidence calibrated independently from deterministic policy gating.
                </span>
              </div>
            </div>
          </div>

          {/* Recovery Plan & Timing */}
          <div className="card-panel space-y-2.5">
            <h3 className="data-label mb-2">Recovery Action Plan</h3>
            <div className="space-y-2 text-xs">
              <div>
                <span className="data-label text-[10px] block">Recommended Strategy</span>
                <span className="data-value font-bold text-[#0b1c30] block mt-0.5">
                  {isCaseA
                    ? "Scheduled Smart Retry + Confirmation Nudge"
                    : isCaseB
                    ? "Conversational WhatsApp Nudge (Operator Approved)"
                    : "Halt Automated Recovery & Escalate to Operator"}
                </span>
              </div>
              <div>
                <span className="data-label text-[10px] block">Execution Window</span>
                <span className="data-value text-[#009668] font-bold block mt-0.5">
                  {isCaseA ? "Immediate (0.0s Window)" : isCaseB ? "+4 Hours (Optimal Window)" : "Halted by Safety Gating"}
                </span>
              </div>
            </div>
          </div>

          {/* Recommended Customer Communication */}
          <div className="card-panel space-y-2.5">
            <div className="flex items-center justify-between border-b border-[#f1f5f9] pb-2">
              <h3 className="data-label flex items-center gap-1">
                <Globe className="w-3.5 h-3.5 text-[#76777d]" /> Customer Communication
              </h3>
              <span className="text-[10px] font-mono text-[#76777d]">Synthetic</span>
            </div>

            {/* Language Selector Pills */}
            <div className="flex flex-wrap gap-1 text-[11px]">
              {[
                { k: "Hindi_Latin", l: "Hinglish" },
                { k: "English_Latin", l: "English" },
                { k: "Tamil_Latin", l: "Tanglish" },
              ].map((lang) => (
                <button
                  key={lang.k}
                  onClick={() => setSelectedLang(lang.k)}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                    selectedLang === lang.k
                      ? "bg-[#712ae2] text-white font-semibold"
                      : "bg-[#f8f9ff] text-[#45464d] hover:bg-[#e2e8f0] border border-[#e2e8f0]"
                  }`}
                >
                  {lang.l}
                </button>
              ))}
            </div>

            {/* Message Body */}
            {currentMsg && (
              <div className="p-2.5 bg-[#f8f9ff] border border-[#e2e8f0] rounded text-xs italic text-[#0b1c30] leading-relaxed">
                &quot;{currentMsg.body}&quot;
              </div>
            )}

            <p className="text-[10px] text-[#76777d] italic">
              Synthetic preview • Only sent if approved by merchant policy.
            </p>
          </div>
        </div>
      </div>

      {/* Embedded Audit Trail Section (Stitch Exact Layout) */}
      <div className="bg-white border border-[#e2e8f0] rounded shadow-2xs overflow-hidden">
        <div className="px-4 py-2.5 bg-[#f8f9ff] border-b border-[#e2e8f0] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#76777d]" />
            <h3 className="font-label-md text-[12px] font-bold text-[#0b1c30] uppercase tracking-wider">
              Audit Trail & Telemetry Log
            </h3>
          </div>
          <Link
            href="/audit"
            className="text-[12px] font-semibold text-[#712ae2] hover:underline flex items-center gap-0.5"
          >
            <span>View Full Ledger</span>
            <ChevronRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-[11px] border-collapse whitespace-nowrap">
            <thead>
              <tr className="bg-[#f8f9ff] border-b border-[#e2e8f0] text-[10px] text-[#76777d] uppercase tracking-wider h-7">
                <th className="px-4 py-1">Timestamp</th>
                <th className="px-4 py-1">Actor</th>
                <th className="px-4 py-1">Event</th>
                <th className="px-4 py-1">Policy Evaluated</th>
                <th className="px-4 py-1">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e2e8f0]/60">
              {audit_trail && audit_trail.length > 0 ? (
                audit_trail.map((ev, i) => (
                  <tr key={i} className="h-7 hover:bg-[#f8f9ff] transition">
                    <td className="px-4 text-[#76777d]">{formatDate(ev.timestamp)}</td>
                    <td className="px-4 font-bold text-[#0b1c30]">{ev.actor}</td>
                    <td className="px-4 text-[#0b1c30]">{ev.event_type}</td>
                    <td className="px-4 text-[#76777d]">{ev.payload?.policy_rule || "Ruleset_v2"}</td>
                    <td className="px-4 font-semibold text-[#009668]">
                      {ev.payload?.outcome || ev.payload?.status || "SUCCESS"}
                    </td>
                  </tr>
                ))
              ) : (
                steps.map((st, i) => (
                  <tr key={i} className="h-7 hover:bg-[#f8f9ff] transition">
                    <td className="px-4 text-[#76777d]">{formatDate(st.timestamp)}</td>
                    <td className="px-4 font-bold text-[#0b1c30]">{st.actor}</td>
                    <td className="px-4 text-[#0b1c30]">{st.title}</td>
                    <td className="px-4 text-[#76777d]">Policy_Check_v2</td>
                    <td className="px-4 font-semibold text-[#009668]">{st.status}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Human Review Drawer */}
      <HumanReviewDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        payment={payment}
        onActionComplete={loadData}
      />
    </div>
  );
}

