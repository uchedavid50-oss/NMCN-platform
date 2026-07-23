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
  if (response.status === 204) return undefined as T;
  return response.json();
}

// ---- CGPA Calculator ----

export interface CourseOut {
  id: string;
  semester: string;
  course_name: string;
  credit_units: number;
  grade: string;
}
export interface SemesterSummary {
  semester: string;
  total_units: number;
  grade_points: number;
  gpa: number;
}
export interface CGPASummary {
  cgpa: number;
  total_units: number;
  semesters: SemesterSummary[];
  courses: CourseOut[];
}

export function getCGPASummary(token: string) {
  return request<CGPASummary>("/cgpa/summary", {}, token);
}

export function addCourse(
  semester: string,
  courseName: string,
  creditUnits: number,
  grade: string,
  token: string
) {
  return request<CourseOut>(
    "/cgpa/courses",
    {
      method: "POST",
      body: JSON.stringify({
        semester,
        course_name: courseName,
        credit_units: creditUnits,
        grade,
      }),
    },
    token
  );
}

export function deleteCourse(courseId: string, token: string) {
  return request<void>(`/cgpa/courses/${courseId}`, { method: "DELETE" }, token);
}

// ---- Mnemonic Generator ----

export interface Mnemonic {
  id: string;
  term: string;
  mnemonic_text: string;
  created_at: string;
}

export function listMnemonics(token: string) {
  return request<Mnemonic[]>("/mnemonics", {}, token);
}

export function generateMnemonic(term: string, token: string) {
  return request<Mnemonic>(
    "/mnemonics/generate",
    { method: "POST", body: JSON.stringify({ term }) },
    token
  );
}

// ---- Focus Sessions ----

export interface FocusSessionResult {
  total_sessions: number;
  total_minutes: number;
  current_streak: number;
}

export function completeFocusSession(durationMinutes: number, token: string) {
  return request<FocusSessionResult>(
    "/focus/complete",
    { method: "POST", body: JSON.stringify({ duration_minutes: durationMinutes }) },
    token
  );
}
