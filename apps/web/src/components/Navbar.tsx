"use client";

import React, { useState } from "react";
import { DemoScenarioSelector } from "./DemoScenarioSelector";
import { GlobalSearchModal } from "./GlobalSearchModal";
import { seedDemoDataset } from "@/lib/api";
import {
  Search,
  RefreshCw,
  CheckCircle2,
  Bell,
  HelpCircle,
} from "lucide-react";

export function Navbar() {
  const [seeding, setSeeding] = useState(false);
  const [seedSuccess, setSeedSuccess] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      await seedDemoDataset();
      setSeedSuccess(true);
      setTimeout(() => {
        setSeedSuccess(false);
        window.location.reload();
      }, 800);
    } catch (err) {
      console.error("Failed to seed demo data", err);
    } finally {
      setSeeding(false);
    }
  };

  return (
    <>
      <header className="h-12 border-b border-[#e2e8f0] bg-white sticky top-0 z-30 flex items-center justify-between px-6 select-none shadow-subtle">
        {/* Left: RecoverX Title, Environment Pill & Scenario Switcher */}
        <div className="flex items-center gap-6 h-full">
          <div className="flex items-center gap-2">
            <span className="text-[13px] font-bold text-[#0b1c30] tracking-tight">RecoverX</span>
            <span className="text-[#c6c6cd]">•</span>
            <span className="text-[11px] font-mono font-semibold px-1.5 py-0.5 rounded bg-[#eff4ff] text-[#712ae2] border border-[#d3e4fe]">
              SANDBOX
            </span>
          </div>

          <div className="h-4 w-px bg-[#e2e8f0] hidden lg:block" />

          <DemoScenarioSelector />
        </div>

        {/* Right: Search, Reset, Notifications & Merchant Profile */}
        <div className="flex items-center gap-3">
          {/* Global Search Button */}
          <button
            onClick={() => setSearchOpen(true)}
            className="flex items-center gap-2 px-2.5 py-1 rounded bg-[#f8f9ff] hover:bg-[#eff4ff] border border-[#e2e8f0] text-[12px] text-[#45464d] hover:text-[#0b1c30] transition shadow-2xs"
            title="Search payments (⌘K)"
          >
            <Search className="w-3.5 h-3.5 text-[#76777d]" />
            <span className="hidden md:inline">Search...</span>
            <kbd className="px-1 py-0.2 text-[10px] font-mono bg-white border border-[#e2e8f0] rounded text-[#76777d]">
              ⌘K
            </kbd>
          </button>

          {/* Seed / Reset Demo Button */}
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-white hover:bg-[#f8f9ff] text-[#0b1c30] border border-[#e2e8f0] text-[11px] font-semibold transition disabled:opacity-50"
            title="Reset and re-seed sample failure events"
          >
            {seedSuccess ? (
              <>
                <CheckCircle2 className="w-3 h-3 text-[#009668]" />
                <span>Reset!</span>
              </>
            ) : (
              <>
                <RefreshCw
                  className={`w-3 h-3 text-[#76777d] ${
                    seeding ? "animate-spin text-[#712ae2]" : ""
                  }`}
                />
                <span className="hidden sm:inline">Reset</span>
              </>
            )}
          </button>

          {/* Notifications */}
          <button
            aria-label="Notifications"
            className="p-1.5 rounded hover:bg-[#f8f9ff] text-[#76777d] hover:text-[#0b1c30] transition relative"
          >
            <Bell className="w-4 h-4" />
            <span className="w-1.5 h-1.5 rounded-full bg-[#712ae2] absolute top-1 right-1" />
          </button>

          {/* Help / Docs */}
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            aria-label="Help Documentation"
            className="p-1.5 rounded hover:bg-[#f8f9ff] text-[#76777d] hover:text-[#0b1c30] transition hidden sm:block"
          >
            <HelpCircle className="w-4 h-4" />
          </a>

          <div className="h-4 w-px bg-[#e2e8f0]" />

          {/* Merchant Profile */}
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-[#131b2e] text-white flex items-center justify-center text-[10px] font-bold font-mono">
              RX
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-[11px] font-bold text-[#0b1c30] leading-tight">Merchant Ops</div>
            </div>
          </div>
        </div>
      </header>

      {/* Global Search Modal */}
      <GlobalSearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}

