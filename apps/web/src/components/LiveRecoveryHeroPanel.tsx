"use client";

import React, { useState } from "react";
import Link from "next/link";
import { formatINR } from "@/lib/utils";
import {
  ShieldCheck,
  UserCheck,
  AlertTriangle,
  Cpu,
  Zap,
  CheckCircle2,
  XCircle,
  MessageSquare,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Scale,
  ExternalLink,
  Layers,
} from "lucide-react";

export type DemoCaseKey = "case_a" | "case_b" | "case_c";

interface DemoCaseDetail {
  key: DemoCaseKey;
  tag: string;
  autonomyLevel: "AUTONOMOUS" | "ASSISTED" | "ESCALATED";
  orderId: string;
  paymentId: string;
  customerName: string;
  customerSegment: string;
  paymentMethod: string;
  amount: number;
  failureReason: string;
  failureCode: string;
  aiDiagnosis: string;
  evidence: string;
  confidence: number;
  policyDecision: "APPROVE" | "ESCALATE" | "BLOCK";
  recommendedAction: string;
  whyExplanation: string;
  policyChecks: Array<{ name: string; passed: boolean; note: string }>;
  language: string;
  script: string;
  tone: string;
  messageHeadline: string;
  messageBody: string;
  messageCta: string;
  outcomeStatus: "RECOVERED" | "IN_REVIEW" | "BLOCKED";
  outcomeMessage: string;
  outcomeAmount?: number;
  timestamp: string;
}

const DEMO_CASES: Record<DemoCaseKey, DemoCaseDetail> = {
  case_a: {
    key: "case_a",
    tag: "CASE A — AUTONOMOUS",
    autonomyLevel: "AUTONOMOUS",
    orderId: "order_demo_case_a_high_conf",
    paymentId: "pay_demo_case_a_high_conf",
    customerName: "Priya Sharma",
    customerSegment: "DIRECT_TO_CONSUMER",
    paymentMethod: "UPI",
    amount: 3499.0,
    failureReason: "NPCI UPI Switch timed out waiting for Issuing Bank response",
    failureCode: "NPCI_ERR_91",
    aiDiagnosis: "Transient Bank / NPCI Switch Network Latency",
    evidence: "Specific timeout error code (NPCI_91), 92% historical customer success rate, zero previous retries.",
    confidence: 0.93,
    policyDecision: "APPROVE",
    recommendedAction: "RETRY_NOW",
    whyExplanation: "Transient switch latency + strong historical success pattern (92%) + clean telemetry context.",
    policyChecks: [
      { name: "Retry Limit Check", passed: true, note: "Attempt 1 of 2 max autonomous retries" },
      { name: "Cooldown Window", passed: true, note: "Initial attempt, cooldown satisfied" },
      { name: "Idempotency Key", passed: true, note: "SHA-256 idempotency key verified" },
      { name: "Failure Instrument", passed: true, note: "Non-terminal transient error" },
      { name: "Amount Governance", passed: true, note: "₹3,499.00 < ₹50,000 threshold" },
    ],
    language: "Hindi",
    script: "Latin (Hinglish)",
    tone: "EMPATHETIC",
    messageHeadline: "Order #order_demo_case_a_high_conf ka payment complete nahi ho paya",
    messageBody: "Namaste Priya, aapke Order ka ₹3,499.00 ka payment bank technical issue ki wajah se complete nahi ho saka. Aapka order safe hai.",
    messageCta: "Retry Payment Securely",
    outcomeStatus: "RECOVERED",
    outcomeMessage: "Verified capture settled via simulated bank gateway callback.",
    outcomeAmount: 3499.0,
    timestamp: "Just now (Verified)",
  },
  case_b: {
    key: "case_b",
    tag: "CASE B — ASSISTED",
    autonomyLevel: "ASSISTED",
    orderId: "order_demo_case_b_assisted",
    paymentId: "pay_demo_case_b_assisted",
    customerName: "Karthik Subramanian",
    customerSegment: "SMB",
    paymentMethod: "MANDATE_AUTOPAY",
    amount: 14500.0,
    failureReason: "Debit account balance insufficient for mandate execution (NPCI_ERR_51)",
    failureCode: "NPCI_ERR_51",
    aiDiagnosis: "Insufficient Funds / Salary Balance Timing",
    evidence: "Recurring mandate payment failed due to transient balance timing near end-of-month.",
    confidence: 0.74,
    policyDecision: "APPROVE",
    recommendedAction: "RETRY_SMART_SCHEDULE",
    whyExplanation: "Balance timing error on mandate. Scheduled smart retry + SMS link prevents overdraft decline.",
    policyChecks: [
      { name: "Retry Limit Check", passed: true, note: "Attempt 1 of 2 max retries" },
      { name: "Cooldown Window", passed: true, note: "Scheduled for +4h window" },
      { name: "Idempotency Key", passed: true, note: "Mandate idempotency registered" },
      { name: "Failure Instrument", passed: true, note: "Account active, recoverable" },
      { name: "Amount Governance", passed: true, note: "₹14,500.00 < ₹50,000 threshold" },
    ],
    language: "Tamil",
    script: "Latin (Tanglish)",
    tone: "PROFESSIONAL",
    messageHeadline: "Order #order_demo_case_b_assisted payment notice",
    messageBody: "Vanakkam Karthik, ungal ₹14,500.00 mandate execution balance illatha kaaranathinal complete aagavillai. Smart retry schedule seiyappattullathu.",
    messageCta: "Pay Now via Secure Link",
    outcomeStatus: "IN_REVIEW",
    outcomeMessage: "Enqueued in Assisted Review Queue for scheduled execution.",
    timestamp: "In Queue (Operator Review)",
  },
  case_c: {
    key: "case_c",
    tag: "CASE C — ESCALATED",
    autonomyLevel: "ESCALATED",
    orderId: "order_demo_case_c_high_val_anom",
    paymentId: "pay_demo_case_c_high_val_anom",
    customerName: "Vikram Singhania",
    customerSegment: "VIP_ENTERPRISE",
    paymentMethod: "NETBANKING",
    amount: 85000.0,
    failureReason: "Gateway timeout vs Bank Recon shows PENDING_CAPTURE",
    failureCode: "ERR_CONTRADICTORY_RECON",
    aiDiagnosis: "Contradictory Telemetry & Double-Debit Hazard",
    evidence: "Gateway callback reported TIMEOUT, but bank recon telemetry shows pending capture. High-value enterprise account (₹85,000).",
    confidence: 0.38,
    policyDecision: "ESCALATE",
    recommendedAction: "ESCALATE_HUMAN",
    whyExplanation: "Severe contradiction detected + High-value commercial transaction (₹85,000 >= ₹50,000). Autonomous retry is strictly blocked.",
    policyChecks: [
      { name: "Contradiction Anomaly", passed: false, note: "RULE_7: Conflicting records detected -> ESCALATE" },
      { name: "High-Value Governance", passed: false, note: "RULE_8: Amount ₹85,000 >= ₹50k limit -> ESCALATE" },
      { name: "Duplicate Protection", passed: true, note: "No active retry executing" },
      { name: "Failure Instrument", passed: true, note: "Account valid" },
      { name: "Zero Unsafe Rule", passed: false, note: "Blocked by deterministic policy engine" },
    ],
    language: "English",
    script: "Latin",
    tone: "PROFESSIONAL",
    messageHeadline: "Payment Verification in Progress for Order #order_demo_case_c_high_val_anom",
    messageBody: "Dear Vikram Singhania, your payment of ₹85,000.00 is currently undergoing reconciliation with your bank. Please do not re-attempt payment to prevent duplicate debits.",
    messageCta: "Check Reconciliation Status",
    outcomeStatus: "BLOCKED",
    outcomeMessage: "Automated retry prevented. Case assigned to Senior Operations Desk.",
    timestamp: "Escalated to Operator",
  },
};

export function LiveRecoveryHeroPanel() {
  const [selectedCase, setSelectedCase] = useState<DemoCaseKey>("case_a");
  const activeCase = DEMO_CASES[selectedCase];

  return (
    <div className="rounded-xl bg-white border border-slate-200 shadow-sm overflow-hidden">
      {/* Header Bar with Case Filter Selector */}
      <div className="px-5 py-3.5 bg-slate-50/80 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse" />
          <span className="text-xs font-bold text-slate-900 tracking-tight">
            Live Recovery Decision Drawer
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-[11px] font-medium text-slate-500">
            Interactive Operational Flow
          </span>
        </div>

        {/* 3 Case Modes */}
        <div className="flex items-center gap-1.5 p-1 bg-white rounded-lg border border-slate-200 shadow-2xs">
          <button
            onClick={() => setSelectedCase("case_a")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition flex items-center gap-1.5 ${
              selectedCase === "case_a"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-300 shadow-2xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Case A: Autonomous (0.93)
          </button>
          <button
            onClick={() => setSelectedCase("case_b")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition flex items-center gap-1.5 ${
              selectedCase === "case_b"
                ? "bg-amber-50 text-amber-800 border border-amber-300 shadow-2xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            Case B: Assisted (0.74)
          </button>
          <button
            onClick={() => setSelectedCase("case_c")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition flex items-center gap-1.5 ${
              selectedCase === "case_c"
                ? "bg-rose-50 text-rose-800 border border-rose-300 shadow-2xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
            Case C: Escalated (0.38)
          </button>
        </div>
      </div>

      {/* Visual Pipeline Flow Strip */}
      <div className="px-5 py-3 bg-white border-b border-slate-100 flex items-center justify-between overflow-x-auto text-xs gap-2">
        <div className="flex items-center gap-1.5 text-slate-700 font-semibold shrink-0">
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono font-bold">1</span>
          <span>PAYMENT FAILED</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />

        <div className="flex items-center gap-1.5 text-indigo-700 font-semibold shrink-0">
          <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] font-mono font-bold">2</span>
          <span>AI DIAGNOSED</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />

        <div className="flex items-center gap-1.5 text-indigo-700 font-semibold shrink-0">
          <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] font-mono font-bold">3</span>
          <span>CONFIDENCE ({activeCase.confidence})</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />

        <div className="flex items-center gap-1.5 text-slate-700 font-semibold shrink-0">
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono font-bold">4</span>
          <span>POLICY GATED</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />

        <div className="flex items-center gap-1.5 text-slate-700 font-semibold shrink-0">
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono font-bold">5</span>
          <span>{activeCase.recommendedAction}</span>
        </div>
        <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />

        <div className="flex items-center gap-1.5 font-bold shrink-0">
          {activeCase.outcomeStatus === "RECOVERED" && (
            <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px]">
              ✓ VERIFIED CAPTURE
            </span>
          )}
          {activeCase.outcomeStatus === "IN_REVIEW" && (
            <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[11px]">
              ⏳ IN HUMAN QUEUE
            </span>
          )}
          {activeCase.outcomeStatus === "BLOCKED" && (
            <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 text-[11px]">
              🛡️ SAFETY STOP (0 EXECUTION)
            </span>
          )}
        </div>
      </div>

      {/* Main Content 3-Column Grid */}
      <div className="p-5 grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Column 1: Payment Context & AI Diagnosis */}
        <div className="space-y-4 rounded-lg bg-slate-50/70 p-4 border border-slate-200">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              1. Failure Diagnosis
            </span>
            <span className="text-xs font-mono font-semibold text-slate-700">
              {formatINR(activeCase.amount)}
            </span>
          </div>

          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Customer:</span>
              <span className="font-semibold text-slate-900">{activeCase.customerName}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Method / Step:</span>
              <span className="font-mono text-slate-700">{activeCase.paymentMethod}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Raw Failure:</span>
              <span className="text-slate-800 text-right truncate max-w-[180px]" title={activeCase.failureReason}>
                {activeCase.failureReason}
              </span>
            </div>
          </div>

          <div className="p-3 rounded-md bg-white border border-slate-200 space-y-1 text-xs">
            <div className="flex items-center gap-1.5 text-indigo-700 font-bold text-[11px]">
              <Cpu className="w-3.5 h-3.5 text-indigo-600" />
              AI ROOT CAUSE DIAGNOSIS
            </div>
            <p className="font-semibold text-slate-900 text-xs mt-0.5">
              {activeCase.aiDiagnosis}
            </p>
            <p className="text-[11px] text-slate-500 mt-1">
              <span className="font-medium text-slate-700">Evidence: </span>
              {activeCase.evidence}
            </p>
          </div>
        </div>

        {/* Column 2: Confidence Calibration & Policy Checks */}
        <div className="space-y-4 rounded-lg bg-slate-50/70 p-4 border border-slate-200">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              2. Policy Engine Gating
            </span>
            <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md ${
              activeCase.policyDecision === "APPROVE"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "bg-rose-50 text-rose-800 border border-rose-200"
            }`}>
              {activeCase.policyDecision === "APPROVE" ? "APPROVED" : "ESCALATED / BLOCKED"}
            </span>
          </div>

          {/* Confidence Score Visual Bar */}
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-600 font-medium">Composite Confidence</span>
              <span className="font-bold font-mono text-slate-900">{activeCase.confidence}</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  activeCase.confidence >= 0.85
                    ? "bg-emerald-600"
                    : activeCase.confidence >= 0.60
                    ? "bg-amber-500"
                    : "bg-rose-500"
                }`}
                style={{ width: `${activeCase.confidence * 100}%` }}
              />
            </div>
            <p className="text-[10px] text-slate-500 italic">
              {activeCase.whyExplanation}
            </p>
          </div>

          {/* Policy Checklist */}
          <div className="space-y-1.5 pt-1">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Deterministic Safety Checklist:
            </span>
            <div className="space-y-1">
              {activeCase.policyChecks.map((chk, i) => (
                <div key={i} className="flex items-start gap-1.5 text-[11px]">
                  {chk.passed ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
                  )}
                  <span className="text-slate-700">
                    <strong className="font-medium text-slate-900">{chk.name}:</strong> {chk.note}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Column 3: Communication & Simulated Outcome */}
        <div className="space-y-4 rounded-lg bg-slate-50/70 p-4 border border-slate-200">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              3. Communication & Outcome
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              {activeCase.language} ({activeCase.script})
            </span>
          </div>

          {/* Multilingual Message Preview Box */}
          <div className="p-3 rounded-md bg-white border border-slate-200 space-y-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-900 text-[11px] truncate">
                {activeCase.messageHeadline}
              </span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200">
                {activeCase.tone}
              </span>
            </div>
            <p className="text-[11px] text-slate-700 mt-1 leading-relaxed">
              {activeCase.messageBody}
            </p>
            <div className="pt-1">
              <button className="px-2.5 py-1 rounded bg-indigo-600 text-white text-[10px] font-semibold">
                {activeCase.messageCta}
              </button>
            </div>
          </div>

          {/* Outcome Status Preview */}
          <div className="p-3 rounded-md bg-white border border-slate-200 space-y-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-700">Simulated Outcome:</span>
              <span className="text-[10px] text-slate-400 font-mono">{activeCase.timestamp}</span>
            </div>
            <p className="text-[11px] text-slate-600 leading-snug">
              {activeCase.outcomeMessage}
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Principle Callout */}
      <div className="px-5 py-2.5 bg-indigo-50/50 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-indigo-600" />
          <span className="text-slate-700 font-medium">
            <strong className="text-slate-900">Governance Principle:</strong> AI recommends. Policy authorizes. Humans handle uncertainty.
          </span>
        </div>
        <Link
          href={`/payments/${activeCase.paymentId}`}
          className="flex items-center gap-1 text-xs font-semibold text-indigo-700 hover:text-indigo-800"
        >
          <span>View Full Payment Audit Journey</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
