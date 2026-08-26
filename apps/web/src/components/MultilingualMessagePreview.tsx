import React, { useState } from "react";
import { MultilingualBundle } from "@/lib/types";
import { Globe, ShieldCheck, MessageSquare, Sparkles } from "lucide-react";

interface Props {
  bundle?: MultilingualBundle;
}

const LANGUAGE_TABS = [
  { key: "English_Latin", label: "English", sub: "Latin" },
  { key: "Hindi_Devanagari", label: "हिंदी", sub: "Devanagari" },
  { key: "Hindi_Latin", label: "Hinglish", sub: "Hindi (Latin)" },
  { key: "Tamil_Tamil", label: "தமிழ்", sub: "Tamil" },
  { key: "Tamil_Latin", label: "Tanglish", sub: "Tamil (Latin)" },
  { key: "Telugu_Telugu", label: "తెలుగు", sub: "Telugu" },
  { key: "Kannada_Kannada", label: "ಕನ್ನಡ", sub: "Kannada" },
  { key: "Malayalam_Malayalam", label: "മലയാളം", sub: "Malayalam" },
  { key: "Marathi_Devanagari", label: "मराठी", sub: "Marathi" },
  { key: "Bengali_Bengali", label: "বাংলা", sub: "Bengali" },
  { key: "Gujarati_Gujarati", label: "ગુજરાતી", sub: "Gujarati" },
  { key: "Gujarati_Latin", label: "Gujarati", sub: "Latin" },
];

export function MultilingualMessagePreview({ bundle }: Props) {
  const [activeTab, setActiveTab] = useState<string>("Hindi_Latin");

  if (!bundle || !bundle.messages) {
    return (
      <div className="rounded-xl bg-white border border-slate-200 p-6 text-center text-slate-500 text-xs">
        Loading communication intelligence preview...
      </div>
    );
  }

  const currentMsg = bundle.messages[activeTab] || bundle.messages["English_Latin"];

  return (
    <div className="rounded-xl bg-white border border-slate-200 p-5 shadow-xs">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-100">
            <Globe className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900">Customer Recovery Communication</h3>
            <p className="text-[11px] text-slate-500">Autonomous Multilingual Script & Tone Selection</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-semibold">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          Safety Guardrails Verified
        </div>
      </div>

      {/* Language & Script Selector Tabs */}
      <div className="mt-3 flex flex-wrap gap-1.5 pb-2 border-b border-slate-100">
        {LANGUAGE_TABS.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all flex flex-col items-start ${
                isActive
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              <span className="font-semibold text-[11px] leading-tight">{tab.label}</span>
              <span className={`text-[9px] ${isActive ? "text-indigo-200" : "text-slate-500"}`}>
                {tab.sub}
              </span>
            </button>
          );
        })}
      </div>

      {/* Message Preview Container */}
      {currentMsg && (
        <div className="mt-4 space-y-3">
          <div className="rounded-lg bg-slate-50 border border-slate-200 p-4 relative">
            <div className="absolute top-3 right-3 flex items-center gap-1 px-2 py-0.5 rounded bg-white text-indigo-700 border border-indigo-200 text-[10px] font-semibold">
              <Sparkles className="w-3 h-3 text-indigo-600" />
              Tone: {currentMsg.tone}
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-indigo-100 text-indigo-700 shrink-0">
                <MessageSquare className="w-4 h-4" />
              </div>
              <div className="space-y-2 pr-16">
                <h4 className="text-xs font-bold text-slate-900">
                  {currentMsg.headline}
                </h4>
                <p className="text-xs text-slate-700 leading-relaxed font-sans">
                  {currentMsg.body}
                </p>

                {/* Call to Action Button */}
                <div className="pt-1">
                  <button className="px-3.5 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition">
                    {currentMsg.cta_text} →
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Guardrail Safety Verification Flags */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
            <span className="text-slate-500 font-semibold">Deterministic Policy:</span>
            {currentMsg.validation_flags.map((flag, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200 text-[10px] font-mono text-emerald-800 font-medium"
              >
                ✓ {flag}
              </span>
            ))}
          </div>

          {/* Simulation Disclaimer */}
          <p className="text-[10px] text-slate-500 italic">
            ℹ️ {currentMsg.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
