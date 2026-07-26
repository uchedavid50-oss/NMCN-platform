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

export interface TopicNote {
  id: string;
  topic_id: string;
  content: string;
  updated_at: string;
}

export function getTopicNote(topicId: string, token: string) {
  return request<TopicNote>(`/topic-notes/${topicId}`, {}, token);
}

export function generateTopicNote(topicId: string, token: string) {
  return request<TopicNote>(
    "/topic-notes/generate",
    { method: "POST", body: JSON.stringify({ topic_id: topicId }) },
    token
  );
}