"use client";

import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { AuthGate } from "@/components/AuthGate";

export function ClientShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen min-w-0 pl-[240px]">
        <Navbar />
        <main className="flex-1 p-6 overflow-y-auto w-full max-w-[1600px] mx-auto">
          {children}
        </main>
      </div>
    </AuthGate>
  );
}
