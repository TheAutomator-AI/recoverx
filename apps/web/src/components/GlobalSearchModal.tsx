"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, CreditCard, User, AlertCircle, ArrowRight, X } from "lucide-react";
import { fetchPayments } from "@/lib/api";
import { Payment } from "@/lib/types";
import { formatINR } from "@/lib/utils";

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GlobalSearchModal({ isOpen, onClose }: GlobalSearchModalProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetchPayments()
        .then((data) => setPayments(data))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (isOpen) onClose();
        else {
          // Open handled by parent
        }
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filteredPayments = payments.filter((p) => {
    const q = query.toLowerCase();
    return (
      p.id.toLowerCase().includes(q) ||
      p.order_id.toLowerCase().includes(q) ||
      (p.customer_name && p.customer_name.toLowerCase().includes(q)) ||
      p.failure_reason.toLowerCase().includes(q)
    );
  }).slice(0, 6);

  const handleSelect = (paymentId: string) => {
    onClose();
    router.push(`/payments/${paymentId}`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-slate-900/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden animate-in fade-in-0 zoom-in-95 duration-150">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-slate-200 gap-3">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search payments, order IDs, customers, or error codes..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            className="flex-1 text-sm text-slate-900 placeholder-slate-400 bg-transparent border-none outline-none font-medium"
          />
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results Body */}
        <div className="max-h-80 overflow-y-auto p-2">
          {loading ? (
            <div className="py-8 text-center text-xs text-slate-500 font-medium">
              Loading merchant records...
            </div>
          ) : filteredPayments.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">
              {query ? `No transactions found matching "${query}"` : "Type a query to search transactions"}
            </div>
          ) : (
            <div className="space-y-1">
              <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Matching Transactions
              </div>
              {filteredPayments.map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleSelect(p.id)}
                  className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 text-left transition group border border-transparent hover:border-slate-200"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-xs shrink-0">
                      ₹
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-slate-900 truncate">
                          {p.customer_name || "Customer"}
                        </span>
                        <span className="text-[11px] font-mono text-slate-400">
                          #{p.order_id}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 truncate mt-0.5">
                        {p.failure_reason}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0 ml-3">
                    <span className="text-xs font-bold text-slate-900">
                      {formatINR(p.amount)}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-400">
          <span>Search RecoverX payment records</span>
          <div className="flex items-center gap-2 font-mono text-[10px]">
            <kbd className="px-1.5 py-0.5 bg-white rounded border border-slate-200">ESC</kbd> to close
          </div>
        </div>
      </div>
    </div>
  );
}
