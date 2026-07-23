"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ApiError } from "@/lib/api";
import {
  listTextbookFolders,
  createTextbookFolder,
  listTextbooksInFolder,
  uploadTextbook,
  deleteTextbook,
  getTextbookDownloadUrl,
  TextbookFolder,
  Textbook,
} from "@/lib/api-extras-2";

export default function TextbooksPage() {
  const { user, token, loading } = useRequireAuth();
  const [folders, setFolders] = useState<TextbookFolder[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [textbooks, setTextbooks] = useState<Textbook[]>([]);
  const [newFolderName, setNewFolderName] = useState("");
  const [uploadTitle, setUploadTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function refreshFolders() {
    if (!token) return;
    listTextbookFolders(token).then(setFolders).catch(() => {});
  }

  useEffect(() => {
    if (!user || !token) return;
    refreshFolders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, token]);

  useEffect(() => {
    if (!token || !selectedFolderId) return;
    listTextbooksInFolder(selectedFolderId, token).then(setTextbooks).catch(() => {});
  }, [token, selectedFolderId]);

  async function handleCreateFolder() {
    if (!token || !newFolderName.trim()) return;
    try {
      await createTextbookFolder(newFolderName, token);
      setNewFolderName("");
      refreshFolders();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't create this folder.");
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token || !selectedFolderId || !uploadTitle.trim()) return;
    setUploading(true);
    setError(null);
    try {
      await uploadTextbook(selectedFolderId, uploadTitle, file, token);
      setUploadTitle("");
      listTextbooksInFolder(selectedFolderId, token).then(setTextbooks);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(id: string) {
    if (!token || !selectedFolderId) return;
    try {
      await deleteTextbook(id, token);
      listTextbooksInFolder(selectedFolderId, token).then(setTextbooks);
    } catch {
      setError("Couldn't delete this textbook.");
    }
  }

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Textbook Library</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Browse and download nursing textbooks
      </h1>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      {user.role === "admin" && (
        <div className="mt-6 rounded-md border border-mist bg-card-bg p-5">
          <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
            Admin: create a folder
          </p>
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Folder name (e.g. Anatomy & Physiology)"
              className="flex-1 rounded-md border border-mist px-3 py-2 text-sm"
            />
            <button
              onClick={handleCreateFolder}
              className="rounded-md bg-vital-teal px-4 py-2 text-sm font-medium text-chart-cream hover:bg-ink-navy"
            >
              Create
            </button>
          </div>
        </div>
      )}

      <div className="mt-8 flex flex-wrap gap-2">
        {folders.map((f) => (
          <button
            key={f.id}
            onClick={() => setSelectedFolderId(f.id)}
            className={`rounded-md border px-4 py-2 text-sm font-medium transition ${
              selectedFolderId === f.id
                ? "border-vital-teal bg-vital-teal/10 text-vital-teal"
                : "border-mist text-ink-navy hover:border-vital-teal"
            }`}
          >
            {f.name}
          </button>
        ))}
        {folders.length === 0 && <p className="text-graphite">No folders yet.</p>}
      </div>

      {selectedFolderId && (
        <section className="mt-6">
          {user.role === "admin" && (
            <div className="mb-4 rounded-md border border-mist bg-card-bg p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="Textbook title"
                  className="flex-1 rounded-md border border-mist px-3 py-2 text-sm"
                />
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleUpload}
                  disabled={uploading || !uploadTitle.trim()}
                  className="text-sm"
                />
              </div>
              {uploading && <p className="mt-2 text-sm text-graphite">Uploading…</p>}
            </div>
          )}

          <div className="flex flex-col gap-2">
            {textbooks.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between rounded-md border border-mist px-4 py-3"
              >
                <div>
                  <p className="text-ink-navy">{t.title}</p>
                  <p className="text-xs text-graphite">{(t.file_size / 1024 / 1024).toFixed(1)} MB</p>
                </div>
                <div className="flex items-center gap-3">
                  <a
                    href={getTextbookDownloadUrl(t.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-md bg-vital-teal px-4 py-2 text-sm font-medium text-chart-cream hover:bg-ink-navy"
                  >
                    View / Download
                  </a>
                  {user.role === "admin" && (
                    <button
                      onClick={() => handleDelete(t.id)}
                      className="text-sm text-pulse-coral hover:underline"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            ))}
            {textbooks.length === 0 && (
              <p className="text-graphite">No textbooks in this folder yet.</p>
            )}
          </div>
        </section>
      )}

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
