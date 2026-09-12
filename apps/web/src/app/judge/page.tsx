"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { fetchLatestEvaluation, runEvaluation } from "@/lib/api";
import type { BenchmarkReport, StrategyEvaluationResult } from "@/lib/types";
import { formatINR } from "@/lib/utils";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Gauge,
  Play,
  ShieldCheck,
  Sparkles,
  Target,
  Trophy,
  XCircle,
} from "lucide-react";

function pct(value: number) {
  return `${value.toFixed(1)}%`;
}

function getResult(report: BenchmarkReport | null, key: string): StrategyEvaluationResult | null {
  return report?.strategies?.[key] ?? null;
}

export default function JudgeCenterPage() {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (size = 10000) => {
    setRunning(true);
    setError(null);
    try {
      const next = await runEvaluation(size, 42);
      setReport(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark unavailable");
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    fetchLatestEvaluation()
      .then((latest) => {
        if (latest) setReport(latest);
        else run(10000);
      })
      .catch(() => run(10000));
  }, []);

  const baselineA = getResult(report, "BASELINE_A");
  const baselineB = getResult(report, "BASELINE_B");
  const recoverx = getResult(report, "RECOVERX");

  const proof = useMemo(() => {
    if (!recoverx || !baselineB) return null;
    const uplift = recoverx.business.gross_revenue_recovered - baselineB.business.gross_revenue_recovered;
    const upliftPct = baselineB.business.gross_revenue_recovered > 0
      ? (uplift / baselineB.business.gross_revenue_recovered) * 100
      : 0;
    const safetyPass = recoverx.safety.unsafe_actions_attempted === 0 && recoverx.safety.policy_violations === 0;
    return { uplift, upliftPct, safetyPass };
  }, [baselineB, recoverx]);

  if (!report || !baselineA || !baselineB || !recoverx) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="mx-auto w-8 h-8 rounded-full border-2 border-[#712ae2] border-t-transparent animate-spin" />
          <p className="text-sm font-semibold text-[#0b1c30]">Preparing judge evidence...</p>
          <p className="text-xs text-[#76777d]">Running the same counterfactual harness used by the evaluation view.</p>
        </div>
      </div>
    );
  }

  const rows = [
    {
      label: "Measured gross recovery",
      recoverx: recoverx.business.gross_revenue_recovered,
      baseline: baselineB.business.gross_revenue_recovered,
      format: (v: number) => formatINR(v),
    },
    {
      label: "Recovery rate",
      recoverx: recoverx.business.recovery_rate,
      baseline: baselineB.business.recovery_rate,
      format: pct,
    },
    {
      label: "Unsafe executions",
      recoverx: recoverx.safety.unsafe_actions_attempted,
      baseline: baselineB.safety.unsafe_actions_attempted,
      format: (v: number) => String(v),
    },
    {
      label: "Autonomous precision",
      recoverx: recoverx.ai_reliability.autonomous_precision,
      baseline: baselineB.ai_reliability.autonomous_precision,
      format: pct,
    },
  ];

  return (
    <div className="space-y-5">
      <header className="border-b border-[#e2e8f0] pb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-bold tracking-[0.18em] uppercase text-[#712ae2]">
            <Trophy className="w-4 h-4" />
            Buildathon Judge Center
          </div>
          <h1 className="mt-1 text-[25px] font-semibold tracking-tight text-[#0b1c30]">Proof before polish.</h1>
          <p className="mt-1 max-w-3xl text-sm text-[#45464d]">
            A judge-facing evidence page for measured recovery, safety constraints, AI reliability, and baseline uplift.
            All values below come from the reproducible evaluation harness.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/evaluations" className="px-3 py-2 rounded border border-[#e2e8f0] bg-white text-xs font-semibold text-[#0b1c30] hover:bg-[#f8f9ff]">
            Full Evaluation
          </Link>
          <button
            onClick={() => run(10000)}
            disabled={running}
            className="flex items-center gap-2 px-3 py-2 rounded bg-[#0b1c30] text-white text-xs font-semibold disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${running ? "animate-spin" : ""}`} />
            {running ? "Running 10k..." : "Run 10k Proof"}
          </button>
        </div>
      </header>

      {error && (
        <div className="border border-rose-200 bg-rose-50 text-rose-900 rounded p-3 text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-white border border-[#e2e8f0] rounded p-4">
          <p className="text-[10px] uppercase tracking-wider text-[#76777d] font-bold">Dataset</p>
          <p className="mt-1 text-[22px] font-mono font-bold text-[#0b1c30]">{report.dataset_size.toLocaleString()}</p>
          <p className="text-[11px] text-[#76777d]">seed {report.random_seed} • {report.dataset_version}</p>
        </div>
        <div className="bg-white border border-[#e2e8f0] rounded p-4">
          <p className="text-[10px] uppercase tracking-wider text-[#76777d] font-bold">Revenue at risk</p>
          <p className="mt-1 text-[22px] font-mono font-bold text-[#0b1c30]">{formatINR(recoverx.business.revenue_at_risk)}</p>
          <p className="text-[11px] text-[#76777d]">same cohort for every strategy</p>
        </div>
        <div className="bg-white border border-[#d3e4fe] rounded p-4">
          <p className="text-[10px] uppercase tracking-wider text-[#712ae2] font-bold">RecoverX recovered</p>
          <p className="mt-1 text-[22px] font-mono font-bold text-[#712ae2]">{formatINR(recoverx.business.gross_revenue_recovered)}</p>
          <p className="text-[11px] text-[#45464d]">{recoverx.business.number_of_recoveries.toLocaleString()} successful resolutions</p>
        </div>
        <div className={`border rounded p-4 ${proof?.safetyPass ? "bg-[#ecfdf5] border-[#a7f3d0]" : "bg-rose-50 border-rose-200"}`}>
          <p className="text-[10px] uppercase tracking-wider font-bold">Safety invariant</p>
          <p className="mt-1 text-[22px] font-mono font-bold">{recoverx.safety.unsafe_actions_attempted} unsafe executions</p>
          <p className="text-[11px] font-semibold flex items-center gap-1.5">
            {proof?.safetyPass ? <><CheckCircle2 className="w-3.5 h-3.5" /> policy-safe</> : <><XCircle className="w-3.5 h-3.5" /> investigate</>}
          </p>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="lg:col-span-2 bg-white border border-[#e2e8f0] rounded overflow-hidden">
          <div className="px-4 py-3 border-b border-[#f1f5f9] flex items-center gap-2">
            <Gauge className="w-4 h-4 text-[#712ae2]" />
            <div>
              <h2 className="text-sm font-bold text-[#0b1c30]">Counterfactual comparison</h2>
              <p className="text-[11px] text-[#76777d]">Same events • same simulator • different decision policy</p>
            </div>
          </div>
          <div className="divide-y divide-[#f1f5f9]">
            {rows.map((row) => (
              <div key={row.label} className="grid grid-cols-[1.2fr_.8fr_.8fr] items-center px-4 py-3 gap-4">
                <span className="text-xs font-medium text-[#45464d]">{row.label}</span>
                <span className="text-right text-sm font-mono font-bold text-[#712ae2]">{row.format(row.recoverx)}</span>
                <span className="text-right text-sm font-mono text-[#76777d]">{row.format(row.baseline)}</span>
              </div>
            ))}
            <div className="grid grid-cols-[1.2fr_.8fr_.8fr] px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-[#76777d] bg-[#f8f9ff]">
              <span>Metric</span>
              <span className="text-right text-[#712ae2]">RecoverX</span>
              <span className="text-right">Baseline B</span>
            </div>
          </div>
        </div>

        <div className="bg-[#0b1c30] text-white rounded p-4 space-y-4">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-[#a78bfa]" />
            <span className="text-xs font-bold uppercase tracking-wider">Judge takeaway</span>
          </div>
          <div>
            <p className="text-[11px] text-[#a8b0bf]">Incremental recovery vs fixed rules</p>
            <p className="mt-1 text-[28px] font-mono font-bold">{formatINR(proof?.uplift ?? 0)}</p>
            <p className="text-[11px] text-[#a8b0bf]">{(proof?.upliftPct ?? 0).toFixed(1)}% higher gross recovery on the same cohort</p>
          </div>
          <div className="border-t border-white/10 pt-3 space-y-2 text-[11px]">
            <div className="flex items-center justify-between"><span className="text-[#a8b0bf]">Baseline A</span><span>{formatINR(baselineA.business.gross_revenue_recovered)}</span></div>
            <div className="flex items-center justify-between"><span className="text-[#a8b0bf]">Baseline B</span><span>{formatINR(baselineB.business.gross_revenue_recovered)}</span></div>
            <div className="flex items-center justify-between font-bold"><span>RecoverX</span><span className="text-[#c4b5fd]">{formatINR(recoverx.business.gross_revenue_recovered)}</span></div>
          </div>
          <div className="rounded border border-white/10 bg-white/5 p-3 text-[11px] leading-relaxed text-[#d9deea]">
            RecoverX is not claiming that every failed payment is recoverable. It is maximizing recovery only inside an explicit safety envelope, then escalating when the envelope is not satisfied.
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-white border border-[#e2e8f0] rounded p-4">
          <div className="flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-[#009668]" /><h3 className="text-sm font-bold text-[#0b1c30]">Safety proof</h3></div>
          <p className="mt-2 text-xs text-[#45464d]">Unsafe actions attempted: <strong>{recoverx.safety.unsafe_actions_attempted}</strong>. Policy violations: <strong>{recoverx.safety.policy_violations}</strong>. Blocked actions: <strong>{recoverx.safety.unsafe_actions_blocked}</strong>.</p>
        </div>
        <div className="bg-white border border-[#e2e8f0] rounded p-4">
          <div className="flex items-center gap-2"><Sparkles className="w-4 h-4 text-[#712ae2]" /><h3 className="text-sm font-bold text-[#0b1c30]">AI reliability</h3></div>
          <p className="mt-2 text-xs text-[#45464d]">Autonomous precision <strong>{pct(recoverx.ai_reliability.autonomous_precision)}</strong>, recall <strong>{pct(recoverx.ai_reliability.autonomous_recall)}</strong>, error rate <strong>{pct(recoverx.ai_reliability.autonomous_error_rate)}</strong>.</p>
        </div>
        <div className="bg-white border border-[#e2e8f0] rounded p-4">
          <div className="flex items-center gap-2"><Activity className="w-4 h-4 text-[#712ae2]" /><h3 className="text-sm font-bold text-[#0b1c30]">Operational proof</h3></div>
          <p className="mt-2 text-xs text-[#45464d]">Average simulated recovery time <strong>{recoverx.business.average_recovery_time_minutes.toFixed(1)} min</strong>. Escalation rate <strong>{pct(recoverx.ai_reliability.escalation_rate)}</strong>. Human overturn <strong>{pct(recoverx.ai_reliability.human_overturn_rate)}</strong>.</p>
        </div>
      </section>

      <div className="bg-[#f8f9ff] border border-[#e2e8f0] rounded p-4 text-xs text-[#45464d] flex items-start gap-2">
        <ArrowRight className="w-4 h-4 text-[#712ae2] shrink-0 mt-0.5" />
        <p><strong>Demo integrity:</strong> This page labels the environment as synthetic/simulated by design. Recovery is counted only through the benchmark simulator and deterministic harness; no production customer or real payment data is represented here.</p>
      </div>
    </div>
  );
}
