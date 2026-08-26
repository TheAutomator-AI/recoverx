import {
  AuditEvent,
  DashboardStats,
  EvaluationReport,
  MultilingualBundle,
  Payment,
  PaymentJourneyResponse,
  PromiseToPay,
  ReviewQueueItem,
} from "./types";

/**
 * Canonical API base URL resolver.
 *
 * PRODUCTION (NODE_ENV === "production"):
 * Always returns relative same-origin "/api".
 * Never uses localhost or allows NEXT_PUBLIC_API_URL to override production behavior.
 *
 * DEVELOPMENT (NODE_ENV === "development" or non-production):
 * Uses NEXT_PUBLIC_API_URL if configured, otherwise falls back to http://127.0.0.1:8000/api.
 */
export function getApiBaseUrl(): string {
  if (process.env.NODE_ENV === "production") {
    return "/api";
  }
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!envUrl || envUrl === "/api" || envUrl === "/api/") {
    return "http://127.0.0.1:8000/api";
  }
  const trimmed = envUrl.replace(/\/+$/, "");
  if (trimmed.endsWith("/api")) {
    return trimmed;
  }
  return `${trimmed}/api`;
}

/**
 * User-visible display label for the active API endpoint.
 *
 * In production: "same-origin /api"
 * In development: Configured development URL or "http://127.0.0.1:8000"
 */
export function getApiDisplayUrl(): string {
  if (process.env.NODE_ENV === "production") {
    return "same-origin /api";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
}

export const API_BASE_URL = getApiBaseUrl();
export const API_DISPLAY_URL = getApiDisplayUrl();

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE_URL}/stats/dashboard`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch dashboard stats");
  return res.json();
}

export async function fetchPayments(status?: string): Promise<Payment[]> {
  const url = status
    ? `${API_BASE_URL}/payments?status=${encodeURIComponent(status)}`
    : `${API_BASE_URL}/payments`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch payments");
  return res.json();
}

export async function fetchPaymentJourney(paymentId: string): Promise<PaymentJourneyResponse> {
  const res = await fetch(`${API_BASE_URL}/payments/${paymentId}/journey`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch payment journey");
  return res.json();
}

export async function fetchReviewQueue(): Promise<ReviewQueueItem[]> {
  const res = await fetch(`${API_BASE_URL}/review/queue`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch review queue");
  return res.json();
}

export async function submitReviewAction(
  paymentId: string,
  payload: {
    action: "APPROVE" | "MODIFY" | "REJECT";
    modified_action?: string;
    modified_delay_hours?: number;
    reason: string;
    reviewer_notes?: string;
    review_duration_seconds?: number;
  }
) {
  const res = await fetch(`${API_BASE_URL}/review/${paymentId}/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit review action");
  return res.json();
}

export async function fetchPromises(): Promise<PromiseToPay[]> {
  const res = await fetch(`${API_BASE_URL}/promises`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch promises");
  return res.json();
}

export async function updatePromiseStatus(promiseId: string, status: string, notes?: string) {
  const res = await fetch(`${API_BASE_URL}/promises/${promiseId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, notes }),
  });
  if (!res.ok) throw new Error("Failed to update promise status");
  return res.json();
}

export async function fetchCommunicationPreview(paymentId: string): Promise<MultilingualBundle> {
  const res = await fetch(`${API_BASE_URL}/communication/preview/${paymentId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch communication preview");
  return res.json();
}

export async function runEvaluation(datasetSize = 50, randomSeed = 42): Promise<EvaluationReport> {
  const res = await fetch(
    `${API_BASE_URL}/evaluations/run?dataset_size=${datasetSize}&random_seed=${randomSeed}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error("Failed to run evaluation harness");
  return res.json();
}

export async function fetchAuditEvents(limit = 100): Promise<AuditEvent[]> {
  const res = await fetch(`${API_BASE_URL}/audit?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch audit events");
  return res.json();
}

export async function seedDemoDataset() {
  const res = await fetch(`${API_BASE_URL}/demo/seed`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to seed demo dataset");
  return res.json();
}

export async function fetchDemoCase(caseName: string) {
  const res = await fetch(`${API_BASE_URL}/demo/cases/${caseName}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch ${caseName}`);
  return res.json();
}

export async function fetchRecoveryAttempts(limit = 50) {
  const res = await fetch(`${API_BASE_URL}/recovery/attempts?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch recovery attempts");
  return res.json();
}
