"use client";

import { useEffect, useState } from "react";
import { runEvaluation, fetchLatestEvaluation } from "@/lib/api";
import type { BenchmarkReport } from "@/lib/types";
import { formatINR } from "@/lib/utils";
import { Play, ShieldCheck, AlertTriangle, CheckCircle2, BarChart3 } from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts";

export default function EvaluationsPage() {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [datasetSize, setDatasetSize] = useState(10000);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeHarness = (size = datasetSize) => {
    setRunning(true);
    setError(null);
    runEvaluation(size, 42)
      .then((data) => setReport(data as unknown as BenchmarkReport))
      .catch((err) => {
        console.error("Evaluation error:", err);
        setError(err instanceof Error ? err.message : "Evaluation service is temporarily unavailable.");
      })
      .finally(() => {
        setRunning(false);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchLatestEvaluation()
      .then((latest) => {
        if (latest) {
          setReport(latest);
          setLoading(false);
        } else {
          executeHarness(100);
        }
      })
      .catch(() => executeHarness(100));
  }, []);

  if (loading && !report) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="mx-auto w-8 h-8 rounded-full border-2 border-[#712ae2] border-t-transparent animate-spin" />
          <p className="text-sm font-semibold text-[#0b1c30]">Preparing evaluation...</p>
          <p className="text-xs text-[#76777d]">Loading the latest benchmark report.</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="space-y-4">
        <div className="border border-rose-200 bg-rose-50 rounded p-4 text-sm text-rose-900 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {error || "Evaluation report is unavailable."}
        </div>
        <button onClick={() => executeHarness(100)} disabled={running} className="px-4 py-2 rounded bg-[#0b1c30] text-white text-xs font-semibold disabled:opacity-50">
          {running ? "Running..." : "Retry benchmark"}
        </button>
      </div>
    );
  }

  const baselineA = report.strategies?.BASELINE_A;
  const baselineB = report.strategies?.BASELINE_B;
  const recoverx = report.strategies?.RECOVERX;

  const comparison = [
    {
      metric: "Gross recovery",
      "Baseline A": baselineA?.business.gross_revenue_recovered ?? 0,
      "Baseline B": baselineB?.business.gross_revenue_recovered ?? 0,
      RecoverX: recoverx?.business.gross_revenue_recovered ?? 0,
    },
    {
      metric: "Risk-adjusted recovery",
      "Baseline A": baselineA?.risk_adjusted.risk_adjusted_recovery ?? 0,
      "Baseline B": baselineB?.risk_adjusted.risk_adjusted_recovery ?? 0,
      RecoverX: recoverx?.risk_adjusted.risk_adjusted_recovery ?? 0,
    },
  ];

  return (
    <div className="space-y-5">
      <header className="border-b border-[#e2e8f0] pb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-bold tracking-[0.18em] uppercase text-[#712ae2]">
            <BarChart3 className="w-4 h-4" />
            Evaluation Harness
          </div>
          <h1 className="mt-1 text-[25px] font-semibold tracking-tight text-[#0b1c30]">Benchmark, safety & AI reliability.</h1>
          <p className="mt-1 max-w-3xl text-sm text-[#45464d]">
            RecoverX evaluates the same deterministic synthetic cohort through a naive retry baseline, fixed rules, and the RecoverX policy stack.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={datasetSize}
            onChange={(e) => setDatasetSize(Number(e.target.value))}
            className="px-3 py-2 rounded border border-[#e2e8f0] bg-white text-xs font-semibold text-[#0b1c30]"
          >
            <option value={100}>100 events</option>
            <option value={1000}>1,000 events</option>
            <option value={5000}>5,000 events</option>
            <option value={10000}>10,000 events</option>
          </select>
          <button
            onClick={() => executeHarness()}
            disabled={running}
            className="flex items-center gap-2 px-3 py-2 rounded bg-[#0b1c30] text-white text-xs font-semibold disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${running ? "animate-spin" : ""}`} />
            {running ? "Running..." : "Run benchmark"}
          </button>
        </div>
      </header>

      {error && (
        <div className="border border-amber-200 bg-amber-50 rounded p-3 text-xs text-amber-900 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
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
          <p className="mt-1 text-[22px] font-mono font-bold text-[#0b1c30]">{formatINR(recoverx?.business.revenue_at_risk ?? 0)}</p>
          <p className="text-[11px] text-[#76777d]">shared cohort opportunity</p>
        </div>
        <div className="bg-white border border-[#d3e4fe] rounded p-4">
          <p className="text-[10px] uppercase tracking-wider text-[#712ae2] font-bold">RecoverX recovered</p>
          <p className="mt-1 text-[22px] font-mono font-bold text-[#712ae2]">{formatINR(recoverx?.business.gross_revenue_recovered ?? 0)}</p>
          <p className="text-[11px] text-[#45464d]">{recoverx?.business.number_of_recoveries ?? 0} successful resolutions</p>
        </div>
        <div className="bg-[#ecfdf5] border border-[#a7f3d0] rounded p-4">
          <p className="text-[10px] uppercase tracking-wider text-[#009668] font-bold">Safety invariant</p>
          <p className="mt-1 text-[22px] font-mono font-bold text-[#0b1c30]">{recoverx?.safety.unsafe_actions_attempted ?? 0} unsafe executions</p>
          <p className="text-[11px] font-semibold flex items-center gap-1.5 text-[#166534]"><ShieldCheck className="w-3.5 h-3.5" /> Financial actions remain policy-gated</p>
        </div>
      </section>

      <section className="bg-white border border-[#e2e8f0] rounded p-4">
        <div className="mb-4">
          <h2 className="text-sm font-bold text-[#0b1c30]">Counterfactual recovery comparison</h2>
          <p className="text-[11px] text-[#76777d]">Same cohort • same simulator • different decision strategy</p>
        </div>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={comparison} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis tickFormatter={(v) => `₹${Number(v).toLocaleString()}`} />
              <Tooltip formatter={(v) => formatINR(Number(v))} />
              <Legend />
              <Bar dataKey="Baseline A" />
              <Bar dataKey="Baseline B" />
              <Bar dataKey="RecoverX" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-white border border-[#e2e8f0] rounded p-4">
          <h3 className="text-sm font-bold text-[#0b1c30]">RecoverX AI reliability</h3>
          <div className="mt-3 space-y-2 text-xs text-[#45464d]">
            <p>Autonomous precision: <strong>{(recoverx?.ai_reliability.autonomous_precision ?? 0).toFixed(1)}%</strong></p>
            <p>Autonomous recall: <strong>{(recoverx?.ai_reliability.autonomous_recall ?? 0).toFixed(1)}%</strong></p>
            <p>Error rate: <strong>{(recoverx?.ai_reliability.autonomous_error_rate ?? 0).toFixed(1)}%</strong></p>
          </div>
        </div>
        <div className="bg-white border border-[#e2e8f0] rounded p-4">
          <h3 className="text-sm font-bold text-[#0b1c30]">Human governance</h3>
          <div className="mt-3 space-y-2 text-xs text-[#45464d]">
            <p>Escalation rate: <strong>{(recoverx?.ai_reliability.escalation_rate ?? 0).toFixed(1)}%</strong></p>
            <p>Human overturn: <strong>{(recoverx?.ai_reliability.human_overturn_rate ?? 0).toFixed(1)}%</strong></p>
            <p>Recommendation acceptance: <strong>{(recoverx?.ai_reliability.ai_recommendation_acceptance_rate ?? 0).toFixed(1)}%</strong></p>
          </div>
        </div>
        <div className="bg-white border border-[#e2e8f0] rounded p-4">
          <h3 className="text-sm font-bold text-[#0b1c30]">Constraint proof</h3>
          <div className="mt-3 space-y-2 text-xs text-[#45464d]">
            <p className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-[#009668]" /> Unsafe attempts: <strong>{recoverx?.safety.unsafe_actions_attempted ?? 0}</strong></p>
            <p>Policy violations: <strong>{recoverx?.safety.policy_violations ?? 0}</strong></p>
            <p>Blocked unsafe actions: <strong>{recoverx?.safety.unsafe_actions_blocked ?? 0}</strong></p>
          </div>
        </div>
      </section>

      <div className="bg-[#f8f9ff] border border-[#e2e8f0] rounded p-4 text-xs text-[#45464d]">
        <strong>Integrity note:</strong> this is a synthetic benchmark and simulator. It does not move real money or represent production customer data.
      </div>
    </div>
  );
}
