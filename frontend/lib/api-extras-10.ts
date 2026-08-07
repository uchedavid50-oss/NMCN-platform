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

export const ENTRANCE_EXAM_SUBJECTS = [
  "Biology",
  "Chemistry",
  "Current Affairs",
  "English",
  "Mathematics",
  "Physics",
] as const;

export type EntranceExamSubject = (typeof ENTRANCE_EXAM_SUBJECTS)[number];

export interface EntranceExamQuestion {
  id: string;
  subject: string;
  question_type: string;
  question_text: string;
  model_answer: string;
  explanation: string;
  provider: string | null;
  created_at: string;
}

export function getEntranceExamQuestions(subject: string, count: number, token: string) {
  return request<EntranceExamQuestion[]>(
    `/entrance-exam/questions?subject=${encodeURIComponent(subject)}&count=${count}`,
    {},
    token
  );
}

export interface ProviderRunResult {
  provider: string;
  status: "success" | "failed" | "skipped_no_key" | "skipped_daily_limit";
  questions_generated: number;
  elapsed_seconds: number;
  error: string | null;
}

export interface GenerateBatchResult {
  results: ProviderRunResult[];
  saved_questions: EntranceExamQuestion[];
  total_saved: number;
  total_generated_before_dedup: number;
}

export function generateEntranceExamQuestions(subject: string, token: string) {
  return request<GenerateBatchResult>(
    "/entrance-exam/generate",
    { method: "POST", body: JSON.stringify({ subject }) },
    token
  );
}

export function deleteEntranceExamQuestion(questionId: string, token: string) {
  return request<void>(`/entrance-exam/questions/${questionId}`, { method: "DELETE" }, token);
}

export interface EntranceExamSettings {
  free_questions_per_subject: number;
}

export function getEntranceExamSettings(token: string) {
  return request<EntranceExamSettings>("/entrance-exam/admin/settings", {}, token);
}

export function updateEntranceExamSettings(freeQuestionsPerSubject: number, token: string) {
  return request<EntranceExamSettings>(
    "/entrance-exam/admin/settings",
    { method: "PUT", body: JSON.stringify({ free_questions_per_subject: freeQuestionsPerSubject }) },
    token
  );
}

export interface ProviderStatusEntry {
  name: string;
  configured: boolean;
  status: "healthy" | "failing" | "unknown";
  last_attempt_at: string | null;
  last_error: string | null;
}

export interface ProviderStatus {
  providers: ProviderStatusEntry[];
  last_used: { provider: string; at: string } | null;
  question_counts: { subject: string; count: number }[];
}

export function getProviderStatus(token: string) {
  return request<ProviderStatus>("/entrance-exam/admin/provider-status", {}, token);
}
