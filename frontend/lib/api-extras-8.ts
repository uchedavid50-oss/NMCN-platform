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

export interface TopicVideo {
  id: string;
  topic_id: string;
  youtube_url: string;
  updated_at: string;
}

export function getTopicVideo(topicId: string, token: string) {
  return request<TopicVideo>(`/topic-videos/${topicId}`, {}, token);
}

export function setTopicVideo(topicId: string, youtubeUrl: string, token: string) {
  return request<TopicVideo>(
    `/topic-videos/${topicId}`,
    { method: "PUT", body: JSON.stringify({ youtube_url: youtubeUrl }) },
    token
  );
}
