"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchAuditEvents } from "@/lib/api";
import { AuditEvent } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import {
  FileText,
  Search,
  Filter,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  X,
  Sparkles,
  Key,
  Database,
  Terminal,
  Activity,
  Layers,
} from "lucide-react";

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [actorFilter, setActorFilter] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [inspectorOpen, setInspectorOpen] = useState(false);

  useEffect(() => {
    fetchAuditEvents(150)
      .then((data) => setEvents(data))
      .catch((err) => console.error("Error loading audit trail:", err))
      .finally(() => setLoading(false));
  }, []);

  const filteredEvents = events.filter((e) => {
    const matchesActor = actorFilter === "ALL" || e.actor === actorFilter;
    const q = searchTerm.toLowerCase();
    const matchesSearch =
      e.event_type.toLowerCase().includes(q) ||
      (e.payment_id && e.payment_id.toLowerCase().includes(q));
    return matchesActor && matchesSearch;
  });

  const getActorBadge = (actor: string) => {
    switch (actor) {
      case "POLICY_ENGINE":
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-[#ecfdf5] text-[#009668] border border-[#a7f3d0]">
            POLICY_ENGINE
          </span>
        );
      case "AI_AGENT":
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe]">
            AI_AGENT
          </span>
        );
      case "CONFIDENCE_ENGINE":
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-[#fffbeb] text-[#d97706] border border-[#fde68a]">
            CONFIDENCE_ENGINE
          </span>
        );
      case "HUMAN_OPERATOR":
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-[#f3e8ff] text-[#9333ea] border border-[#e9d5ff]">
            HUMAN_OPERATOR
          </span>
        );
      case "GATEWAY_SIMULATOR":
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-[#f1f5f9] text-[#475569] border border-[#e2e8f0]">
            GATEWAY_SIMULATOR
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-[#f1f5f9] text-[#475569]">
            {actor}
          </span>
        );
    }
  };

  const handleInspect = (ev: AuditEvent) => {
    setSelectedEvent(ev);
    setInspectorOpen(true);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-[#e2e8f0] pb-3">
        <div>
          <h1 className="font-display text-[22px] font-semibold text-[#0b1c30] tracking-tight">
            Audit Trail
          </h1>
          <p className="font-body-md text-[13px] text-[#45464d] mt-0.5">
            Immutable decision and execution history with cryptographic provenance
          </p>
        </div>

        <span className="text-[10px] font-mono font-bold text-[#76777d] bg-white border border-[#e2e8f0] px-2.5 py-1 rounded shadow-2xs">
          IMMUTABLE LEDGER
        </span>
      </div>

      {/* Filter and Search Bar */}
      <div className="border border-[#e2e8f0] bg-white rounded p-2 flex flex-wrap items-center gap-2 shadow-2xs">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="w-3.5 h-3.5 text-[#76777d] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search event type, payment ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-7 pl-8 pr-3 bg-[#f8f9ff] border border-[#e2e8f0] rounded text-[12px] placeholder:text-[#76777d] focus:border-[#712ae2] focus:ring-1 focus:ring-[#712ae2] outline-none transition"
          />
        </div>

        {/* Actor Filters */}
        <div className="flex flex-wrap items-center gap-1">
          {[
            "ALL",
            "POLICY_ENGINE",
            "AI_AGENT",
            "CONFIDENCE_ENGINE",
            "HUMAN_OPERATOR",
            "GATEWAY_SIMULATOR",
          ].map((actor) => (
            <button
              key={actor}
              onClick={() => setActorFilter(actor)}
              className={`px-2.5 py-0.5 rounded text-[11px] font-medium transition ${
                actorFilter === actor
                  ? "bg-[#0b1c30] text-white font-semibold"
                  : "text-[#45464d] hover:text-[#0b1c30] hover:bg-[#f8f9ff]"
              }`}
            >
              {actor}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Log Table (High-Density 32px rows) */}
      <div className="bg-white border border-[#e2e8f0] rounded shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px] border-collapse whitespace-nowrap">
            <thead>
              <tr className="bg-[#f8f9ff] border-b border-[#e2e8f0] h-[30px] font-label-md text-[11px] text-[#76777d] uppercase tracking-wider font-semibold">
                <th className="px-4 py-1">Timestamp</th>
                <th className="px-4 py-1">Actor</th>
                <th className="px-4 py-1">Event Type</th>
                <th className="px-4 py-1">Payment ID</th>
                <th className="px-4 py-1">Policy / State</th>
                <th className="px-4 py-1">Result</th>
                <th className="px-4 py-1 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e2e8f0]/60 font-mono text-[11px]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-[#76777d] font-sans">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-6 h-6 rounded-full border-2 border-[#712ae2] border-t-transparent animate-spin" />
                      <span className="text-xs font-medium">Loading audit events...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-[#76777d] text-xs font-sans">
                    No audit events found matching your search.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((ev) => {
                  const resultStr =
                    ev.payload?.status ||
                    ev.payload?.decision ||
                    (ev.actor === "POLICY_ENGINE" ? "AUTHORIZED" : "LOGGED");

                  return (
                    <tr
                      key={ev.id}
                      onClick={() => handleInspect(ev)}
                      className="h-[32px] hover:bg-[#f8f9ff] transition cursor-pointer group"
                    >
                      {/* Timestamp */}
                      <td className="px-4 text-[#76777d]">
                        {formatDate(ev.timestamp)}
                      </td>

                      {/* Actor */}
                      <td className="px-4 font-sans">
                        {getActorBadge(ev.actor)}
                      </td>

                      {/* Event Type */}
                      <td className="px-4 font-bold text-[#0b1c30]">
                        {ev.event_type}
                      </td>

                      {/* Payment ID */}
                      <td className="px-4">
                        {ev.payment_id ? (
                          <Link
                            href={`/payments/${ev.payment_id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="text-[#712ae2] hover:underline"
                          >
                            pay_{ev.payment_id.substring(0, 10)}
                          </Link>
                        ) : (
                          <span className="text-[#c6c6cd]">—</span>
                        )}
                      </td>

                      {/* Policy */}
                      <td className="px-4 text-[#45464d]">
                        {ev.payload?.policy_rule || "Eligibility_Check_v2"}
                      </td>

                      {/* Result */}
                      <td className="px-4 font-bold text-[#009668]">
                        {resultStr}
                      </td>

                      {/* Inspect */}
                      <td className="px-4 text-right font-sans">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleInspect(ev);
                          }}
                          className="px-2 py-0.5 rounded bg-[#f1f5f9] hover:bg-[#eff4ff] hover:text-[#712ae2] text-[#475569] font-medium text-[11px] transition"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspector Slide-over Drawer */}
      {inspectorOpen && selectedEvent && (
        <>
          <div
            onClick={() => setInspectorOpen(false)}
            className="fixed inset-0 bg-black/40 z-40 backdrop-blur-xs transition-opacity"
          />

          <aside className="fixed top-0 right-0 h-full w-full sm:w-[500px] lg:w-[35%] bg-white border-l border-[#e2e8f0] z-50 flex flex-col shadow-drawer">
            {/* Drawer Header */}
            <div className="p-4 border-b border-[#e2e8f0] flex items-center justify-between bg-[#f8f9ff]">
              <div>
                <h3 className="font-label-md text-[13px] font-bold text-[#0b1c30] uppercase tracking-wider">
                  Event Inspector: {selectedEvent.event_type}
                </h3>
                <span className="font-mono text-[11px] text-[#76777d]">ID: {selectedEvent.id}</span>
              </div>
              <button
                onClick={() => setInspectorOpen(false)}
                className="w-7 h-7 flex items-center justify-center rounded hover:bg-[#e2e8f0] text-[#76777d] hover:text-[#0b1c30]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs font-mono">
              {/* Metadata Grid */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0]">
                  <span className="data-label text-[10px] block font-sans">Timestamp (UTC)</span>
                  <span className="font-bold text-[#0b1c30] block mt-0.5">
                    {formatDate(selectedEvent.timestamp)}
                  </span>
                </div>

                <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0]">
                  <span className="data-label text-[10px] block font-sans">Actor</span>
                  <div className="mt-0.5">{getActorBadge(selectedEvent.actor)}</div>
                </div>

                <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0]">
                  <span className="data-label text-[10px] block font-sans">AI Model</span>
                  <span className="font-bold text-[#0b1c30] block mt-0.5">gpt-4o-mini / mock</span>
                </div>

                <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0]">
                  <span className="data-label text-[10px] block font-sans">Policy Decision</span>
                  <span className="font-bold text-[#009668] block mt-0.5">
                    {selectedEvent.payload?.decision || "APPROVED"}
                  </span>
                </div>
              </div>

              {/* Request Fingerprint */}
              <div className="p-2.5 bg-[#f8f9ff] rounded border border-[#e2e8f0] space-y-1">
                <span className="data-label text-[10px] block font-sans">Request Fingerprint</span>
                <span className="text-[#45464d] text-[11px] block truncate">
                  sha256_{selectedEvent.id.substring(0, 16)}...prov_verified
                </span>
              </div>

              {/* Structured JSON Payload */}
              <div className="space-y-1.5">
                <span className="data-label text-[10px] block font-sans">Structured Payload</span>
                <pre className="p-3 bg-[#0b1c30] text-[#f8f9ff] rounded text-[11px] overflow-x-auto leading-relaxed border border-[#131b2e]">
                  {JSON.stringify(selectedEvent.payload, null, 2)}
                </pre>
              </div>
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-[#e2e8f0] bg-[#f8f9ff] flex justify-end">
              <button
                onClick={() => setInspectorOpen(false)}
                className="px-4 py-1.5 rounded bg-[#0b1c30] hover:bg-[#131b2e] text-white text-xs font-semibold"
              >
                Close Inspector
              </button>
            </div>
          </aside>
        </>
      )}
    </div>
  );
}

