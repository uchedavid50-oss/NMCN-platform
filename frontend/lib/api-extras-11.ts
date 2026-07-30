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
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {
      // no JSON body
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

export interface AdminUser {
  id: string;
  email: string;
  role: string;
  subscription_status: string;
  created_at: string;
}

export interface AdminPayment {
  id: string;
  user_email: string;
  plan: string;
  status: string;
  amount_kobo: number;
  currency: string;
  created_at: string;
  activated_at: string | null;
}

export interface AdminSummary {
  total_students: number;
  total_admins: number;
  signups_today: number;
  active_subscriptions: number;
  total_revenue_kobo: number;
}

export function getRecentUsers(token: string, limit = 50) {
  return request<AdminUser[]>(`/admin/users?limit=${limit}`, {}, token);
}

export function getRecentPayments(token: string, limit = 50) {
  return request<AdminPayment[]>(`/admin/payments?limit=${limit}`, {}, token);
}

export function getAdminSummary(token: string) {
  return request<AdminSummary>("/admin/summary", {}, token);
}
