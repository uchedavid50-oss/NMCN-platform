"use client";

import { ApiError } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // no JSON body
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

export interface InitializePaymentResponse {
  authorization_url: string;
  reference: string;
}

export interface SubscriptionStatus {
  plan: string | null;
  status: string;
  expires_at: string | null;
}

export function initializePayment(plan: string, token: string) {
  return request<InitializePaymentResponse>(
    "/payments/initialize",
    { method: "POST", body: JSON.stringify({ plan }) },
    token
  );
}

export function getSubscriptionStatus(token: string) {
  return request<SubscriptionStatus>("/payments/subscription", {}, token);
}
