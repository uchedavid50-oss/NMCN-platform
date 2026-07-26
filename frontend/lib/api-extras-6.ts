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

export interface PastQuestionOption {
  id: string;
  text: string;
  is_correct: boolean;
}

export interface PastQuestion {
  id: string;
  stem: string;
  explanation: string;
  options: PastQuestionOption[];
}

export function getPastQuestionsCount() {
  return request<{ count: number }>("/past-questions/count", {});
}

export function startPastQuestionsPractice(count: number, token: string) {
  return request<PastQuestion[]>(`/past-questions/practice?count=${count}`, {}, token);
}

export function completePastQuestionsPractice(
  totalQuestions: number,
  correctAnswers: number,
  token: string
) {
  return request<{ score_percentage: number; current_streak: number; played_today: boolean }>(
    "/past-questions/complete",
    { method: "POST", body: JSON.stringify({ total_questions: totalQuestions, correct_answers: correctAnswers }) },
    token
  );
}
