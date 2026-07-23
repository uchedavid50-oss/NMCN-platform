"use client";

import { ApiError } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(options.body && !isFormData ? { "Content-Type": "application/json" } : {}),
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

// ---- Nursing Dictionary ----

export interface DictionaryEntry {
  id: string;
  term: string;
  definition: string;
  is_verified: boolean;
  created_at: string;
}

export function searchDictionary(term: string, token: string) {
  return request<DictionaryEntry>(
    "/dictionary/search",
    { method: "POST", body: JSON.stringify({ term }) },
    token
  );
}

export function listDictionary(query: string, token: string) {
  const q = query ? `?q=${encodeURIComponent(query)}` : "";
  return request<DictionaryEntry[]>(`/dictionary${q}`, {}, token);
}

export function verifyDictionaryEntry(entryId: string, definition: string | null, token: string) {
  return request<DictionaryEntry>(
    `/dictionary/${entryId}/verify`,
    { method: "PATCH", body: JSON.stringify({ definition }) },
    token
  );
}

// ---- Textbook Folders ----

export interface TextbookFolder {
  id: string;
  name: string;
  created_at: string;
}

export interface Textbook {
  id: string;
  folder_id: string;
  title: string;
  filename: string;
  content_type: string;
  file_size: number;
  created_at: string;
}

export function listTextbookFolders(token: string) {
  return request<TextbookFolder[]>("/textbooks/folders", {}, token);
}

export function createTextbookFolder(name: string, token: string) {
  return request<TextbookFolder>(
    "/textbooks/folders",
    { method: "POST", body: JSON.stringify({ name }) },
    token
  );
}

export function listTextbooksInFolder(folderId: string, token: string) {
  return request<Textbook[]>(`/textbooks/folders/${folderId}/textbooks`, {}, token);
}

export function uploadTextbook(folderId: string, title: string, file: File, token: string) {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);
  return request<Textbook>(
    `/textbooks/folders/${folderId}/upload`,
    { method: "POST", body: formData },
    token
  );
}

export function deleteTextbook(textbookId: string, token: string) {
  return request<void>(`/textbooks/${textbookId}`, { method: "DELETE" }, token);
}

export function getTextbookDownloadUrl(textbookId: string) {
  return `${API_URL}/textbooks/${textbookId}/download`;
}
