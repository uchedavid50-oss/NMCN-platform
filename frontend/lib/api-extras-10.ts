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
  created_at: string;
}

export function getEntranceExamQuestions(subject: string, count: number, token: string) {
  return request<EntranceExamQuestion[]>(
    `/entrance-exam/questions?subject=${encodeURIComponent(subject)}&count=${count}`,
    {},
    token
  );
}

export function generateEntranceExamQuestions(subject: string, token: string) {
  return request<EntranceExamQuestion[]>(
    "/entrance-exam/generate",
    { method: "POST", body: JSON.stringify({ subject }) },
    token
  );
}

export function deleteEntranceExamQuestion(questionId: string, token: string) {
  return request<void>(`/entrance-exam/questions/${questionId}`, { method: "DELETE" }, token);
}
