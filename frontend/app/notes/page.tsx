"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, Note } from "@/lib/api";

export default function NotesPage() {
  const { user, token, loading } = useRequireAuth();
  const [notes, setNotes] = useState<Note[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function refreshNotes() {
    if (!token) return;
    api.listNotes(token).then(setNotes).catch(() => setError("Couldn't load your notes."));
  }

  useEffect(() => {
    if (!user || !token) return;
    refreshNotes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, token]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadNote(file, token);
      refreshNotes();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't upload this file.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
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
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">My notes</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Turn your notes into practice questions
      </h1>
      <p className="mt-3 text-graphite">
        Upload a .txt, .pdf, or .docx file of your own study notes, and the AI tutor will generate
        practice questions grounded in what you actually wrote — kept private to you, and clearly
        separate from the official question bank.
      </p>

      <label className="mt-6 inline-block cursor-pointer rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy">
        {uploading ? "Uploading…" : "Upload notes"}
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.pdf,.docx"
          onChange={handleUpload}
          disabled={uploading}
          className="hidden"
        />
      </label>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      <div className="mt-10 flex flex-col gap-3">
        {notes?.map((note) => (
          <Link
            key={note.id}
            href={`/notes/${note.id}`}
            className="flex items-center justify-between rounded-md border border-mist px-5 py-4 transition hover:border-vital-teal"
          >
            <span className="font-body text-ink-navy">{note.filename}</span>
            <span className="text-vital-teal">→</span>
          </Link>
        ))}
        {notes && notes.length === 0 && (
          <p className="text-graphite">No notes uploaded yet — upload one above to get started.</p>
        )}
      </div>

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
