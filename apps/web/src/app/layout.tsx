import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import { Sidebar } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm-plex-sans",
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-ibm-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RecoverX — Payments Revenue Recovery Dashboard",
  description:
    "Production-grade merchant payments dashboard combining AI diagnostic reasoning with deterministic policy gating for failed payment recovery.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${ibmPlexSans.variable} ${ibmPlexMono.variable}`}>
      <body className="bg-background text-on-background min-h-screen antialiased flex selection:bg-secondary-fixed selection:text-on-secondary-fixed font-sans">
        <Sidebar />
        <div className="flex-1 flex flex-col min-h-screen min-w-0 pl-[240px]">
          <Navbar />
          <main className="flex-1 p-6 overflow-y-auto w-full max-w-[1600px] mx-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

