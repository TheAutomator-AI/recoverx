"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CreditCard,
  RotateCcw,
  UserCheck,
  CalendarClock,
  BarChart3,
  FileText,
  Shield,
  Users,
  Search,
  Sparkles,
} from "lucide-react";
import { fetchDashboardStats } from "@/lib/api";

interface NavItem {
  href: string;
  label: string;
  icon: any;
  hasBadge?: boolean;
}

const HOME_NAV: NavItem[] = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
];

const TRANSACTIONS_NAV: NavItem[] = [
  { href: "/payments", label: "Payments", icon: CreditCard },
  { href: "/recovery", label: "Settlements & Retries", icon: RotateCcw },
];

const OPERATIONS_NAV: NavItem[] = [
  { href: "/evaluations", label: "Reports & Analytics", icon: BarChart3 },
  { href: "/promises", label: "Customers & Cohorts", icon: Users },
];

const RECOVERX_NAV: NavItem[] = [
  { href: "/recovery", label: "Recovery", icon: RotateCcw },
  { href: "/review", label: "Review Queue", icon: UserCheck, hasBadge: true },
  { href: "/promises", label: "Promises", icon: CalendarClock },
  { href: "/evaluations", label: "Evaluations", icon: BarChart3 },
  { href: "/audit", label: "Audit", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();
  const [reviewCount, setReviewCount] = useState<number>(0);

  useEffect(() => {
    fetchDashboardStats()
      .then((data) => {
        setReviewCount(data.autonomy_distribution?.["ASSISTED"] || 0);
      })
      .catch(() => {});
  }, []);

  const renderNavGroup = (title: string, items: NavItem[], isRecoverX = false) => (
    <div className="space-y-0.5">
      <div className="px-3 py-1 flex items-center justify-between text-[10px] font-semibold text-[#7c839b] uppercase tracking-wider">
        <span className={isRecoverX ? "text-[#a78bfa] font-bold" : ""}>{title}</span>
        {isRecoverX && <span className="w-1.5 h-1.5 rounded-full bg-[#712ae2]" />}
      </div>
      {items.map((item) => {
        const Icon = item.icon;
        const isActive =
          pathname === item.href ||
          (item.href !== "/dashboard" && pathname.startsWith(item.href));

        return (
          <Link
            key={item.href + item.label}
            href={item.href}
            className={`flex items-center justify-between px-3 py-1.5 rounded text-[13px] font-medium transition-colors ${
              isActive
                ? "bg-[#712ae2] text-white font-semibold shadow-xs"
                : "text-[#7c839b] hover:text-white hover:bg-[#3f465c]/40"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Icon
                className={`w-4 h-4 ${
                  isActive ? "text-white" : "text-[#7c839b] group-hover:text-white"
                }`}
              />
              <span>{item.label}</span>
            </div>
            {item.hasBadge && reviewCount > 0 && (
              <span className={`px-1.5 py-0.2 text-[10px] font-mono font-bold rounded ${
                isActive
                  ? "bg-white/20 text-white"
                  : "bg-amber-400/20 text-amber-300 border border-amber-400/30"
              }`}>
                {reviewCount}
              </span>
            )}
          </Link>
        );
      })}
    </div>
  );

  return (
    <aside className="w-[240px] bg-[#131b2e] border-r border-[#213145] text-[#7c839b] flex flex-col h-screen fixed left-0 top-0 z-40 select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#213145]">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="w-7 h-7 rounded bg-[#712ae2] flex items-center justify-center text-white font-bold shrink-0">
            <Shield className="w-4 h-4 fill-white text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-[14px] font-bold text-white tracking-tight group-hover:text-[#dae2fd] transition">
                RecoverX
              </span>
            </div>
            <p className="text-[11px] text-[#7c839b] font-medium leading-none mt-0.5">
              Payment Operations
            </p>
          </div>
        </Link>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 px-2.5 py-3 space-y-3.5 overflow-y-auto">
        {renderNavGroup("Home", HOME_NAV)}
        {renderNavGroup("Transactions", TRANSACTIONS_NAV)}
        {renderNavGroup("Operations", OPERATIONS_NAV)}
        {renderNavGroup("RecoverX", RECOVERX_NAV, true)}
      </nav>

      {/* Footer System Status */}
      <div className="p-3 border-t border-[#213145] bg-[#0c1424] space-y-2">
        <div className="rounded bg-[#131b2e] border border-[#213145] p-2.5 space-y-1.5 text-xs">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-[#7c839b] font-medium">Policy Engine</span>
            <span className="flex items-center gap-1 text-[#10b981] font-semibold text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse" />
              ACTIVE
            </span>
          </div>
          <div className="flex items-center justify-between border-t border-[#213145] pt-1 text-[11px]">
            <span className="text-[#7c839b] font-medium">Sandbox Mode</span>
            <span className="text-[#dae2fd] font-mono text-[10px] font-semibold">
              SIMULATED
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between px-1 text-[10px] text-[#7c839b]">
          <span className="font-mono">v1.0.0-prod</span>
          <span>•</span>
          <span>RecoverX · Buildathon Edition</span>
        </div>
      </div>
    </aside>
  );
}

