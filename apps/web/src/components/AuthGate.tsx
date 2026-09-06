"use client";

import { useEffect, useState } from "react";
import { onAuthStateChanged, signInWithPopup, User } from "firebase/auth";
import { doc, serverTimestamp, setDoc } from "firebase/firestore";
import { auth, db, googleProvider } from "@/lib/firebase";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => onAuthStateChanged(auth, async (nextUser) => {
    setUser(nextUser);
    setLoading(false);
    if (nextUser) {
      await setDoc(
        doc(db, "users", nextUser.uid),
        {
          uid: nextUser.uid,
          email: nextUser.email ?? null,
          displayName: nextUser.displayName ?? null,
          lastSeenAt: serverTimestamp(),
        },
        { merge: true }
      );
    }
  }), []);

  if (loading) {
    return <div className="min-h-screen grid place-items-center text-sm text-slate-600">Loading RecoverX…</div>;
  }

  if (!user) {
    return (
      <div className="min-h-screen grid place-items-center bg-slate-50 p-6">
        <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
          <div className="mb-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-violet-600">RecoverX</p>
            <h1 className="mt-2 text-2xl font-bold text-slate-900">Secure AI Revenue Recovery</h1>
            <p className="mt-2 text-sm text-slate-600">Sign in to access your authenticated RecoverX workspace.</p>
          </div>
          <button
            onClick={async () => {
              setError("");
              try {
                await signInWithPopup(auth, googleProvider);
              } catch (err) {
                setError(err instanceof Error ? err.message : "Sign-in failed");
              }
            }}
            className="w-full rounded-md bg-violet-600 px-4 py-3 text-sm font-semibold text-white hover:bg-violet-700"
          >
            Continue with Google
          </button>
          {error && <p className="mt-3 text-xs text-red-600">{error}</p>}
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
