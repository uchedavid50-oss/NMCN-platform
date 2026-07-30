"use client";

import { ApiError } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
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

export interface Equipment {
  id: string;
  title: string;
  description: string;
  youtube_url: string | null;
  pdf_filename: string | null;
  updated_at: string;
}

export function getEquipment(token: string) {
  return request<Equipment>("/equipment", {}, token);
}

export function setEquipment(
  title: string,
  description: string,
  youtubeUrl: string,
  token: string
) {
  return request<Equipment>(
    "/equipment",
    { method: "PUT", body: JSON.stringify({ title, description, youtube_url: youtubeUrl || null }) },
    token
  );
}

export function uploadEquipmentPdf(file: File, token: string) {
  const formData = new FormData();
  formData.append("file", file);
  return request<Equipment>("/equipment/pdf", { method: "POST", body: formData }, token);
}

export async function downloadEquipmentPdf(token: string) {
  const response = await fetch(`${API_URL}/equipment/pdf`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new ApiError(response.status, "Couldn't download the equipment PDF.");
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  window.open(url, "_blank");
  setTimeout(() => window.URL.revokeObjectURL(url), 10000);
}

export interface Organ {
  id: string;
  name: string;
  description: string;
}

export interface OrganVideo {
  id: string;
  organ_id: string;
  youtube_url: string;
  updated_at: string;
}

export function getOrgans(token: string) {
  return request<Organ[]>("/organs", {}, token);
}

export function getOrganVideo(organId: string, token: string) {
  return request<OrganVideo>(`/organs/${organId}/video`, {}, token);
}

export function setOrganVideo(organId: string, youtubeUrl: string, token: string) {
  return request<OrganVideo>(
    `/organs/${organId}/video`,
    { method: "PUT", body: JSON.stringify({ youtube_url: youtubeUrl }) },
    token
  );
}
