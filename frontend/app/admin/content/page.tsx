"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import {
  api,
  ApiError,
  AdminDocument,
  BulkImportResult,
  PendingQuestionOut,
  Topic,
} from "@/lib/api";

export default function AdminContentPage() {
  const { user, token, loading } = useRequireAuth();

  const [topics, setTopics] = useState<Topic[]>([]);
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [pending, setPending] = useState<PendingQuestionOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [csvUploading, setCsvUploading] = useState(false);
  const [csvResult, setCsvResult] = useState<BulkImportResult | null>(null);
  const csvInputRef = useRef<HTMLInputElement>(null);

  const [docUploading, setDocUploading] = useState(false);
  const [docType, setDocType] = useState("textbook");
  const docInputRef = useRef<HTMLInputElement>(null);

  const [selectedDocId, setSelectedDocId] = useState("");
  const [selectedTopicId, setSelectedTopicId] = useState("");
  const [genCount, setGenCount] = useState(10);
  const [generating, setGenerating] = useState(false);

  function refreshAll() {
    if (!token) return;
    api.listAllTopics().then(setTopics).catch(() => {});
    api.listAdminDocuments(token).then(setDocuments).catch(() => {});
    api.listPendingQuestions(token).then(setPending).catch(() => {});
  }

  useEffect(() => {
    if (!user || !token) return;
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, token]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  if (user.role !== "admin") {
    return (
      <main className="mx-auto max-w-xl px-6 py-16 text-center">
        <p className="text-pulse-coral">This page is admin-only.</p>
        <Link href="/dashboard" className="mt-4 inline-block text-vital-teal hover:underline">
          ← Back to dashboard
        </Link>
      </main>
    );
  }

  async function handleCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    setCsvUploading(true);
    setError(null);
    setCsvResult(null);
    try {
      const result = await api.bulkImportQuestions(file, token);
      setCsvResult(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "CSV import failed.");
    } finally {
      setCsvUploading(false);
      if (csvInputRef.current) csvInputRef.current.value = "";
    }
  }

  async function handleDocUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    setDocUploading(true);
    setError(null);
    try {
      await api.uploadAdminDocument(file, docType, token);
      refreshAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Document upload failed.");
    } finally {
      setDocUploading(false);
      if (docInputRef.current) docInputRef.current.value = "";
    }
  }

  async function handleGenerate() {
    if (!token || !selectedDocId || !selectedTopicId) return;
    setGenerating(true);
    setError(null);
    try {
      await api.generatePendingQuestions(selectedDocId, selectedTopicId, genCount, token);
      refreshAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Generation failed.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleApprove(id: string) {
    if (!token) return;
    try {
      await api.approvePendingQuestion(id, token);
      refreshAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't approve.");
    }
  }

  async function handleReject(id: string) {
    if (!token) return;
    try {
      await api.rejectPendingQuestion(id, token);
      refreshAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't reject.");
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Admin</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">Content pipeline</h1>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      {/* CSV bulk import */}
      <section className="mt-8 rounded-md border border-mist bg-card-bg p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
          Bulk import (already-vetted content)
        </p>
        <p className="mt-1 text-sm text-graphite">
          CSV columns: subject, topic, stem, difficulty, explanation, option_a, option_b, option_c,
          option_d, correct_answer (a/b/c/d). Publishes directly — no review step.
        </p>
        <input
          ref={csvInputRef}
          type="file"
          accept=".csv"
          onChange={handleCsvUpload}
          disabled={csvUploading}
          className="mt-3 text-sm"
        />
        {csvResult && (
          <div className="mt-3 text-sm">
            <p className="text-vital-teal">Created {csvResult.created_count} questions.</p>
            {csvResult.skipped_rows.length > 0 && (
              <ul className="mt-1 list-disc pl-5 text-pulse-coral">
                {csvResult.skipped_rows.map((row, i) => (
                  <li key={i}>{row}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>

      {/* Document upload + AI generation */}
      <section className="mt-6 rounded-md border border-mist bg-card-bg p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
          Generate from a document (goes to review queue)
        </p>

        <div className="mt-3 flex items-center gap-2">
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="rounded-md border border-mist px-2 py-2 text-sm"
          >
            <option value="textbook">Textbook</option>
            <option value="past_questions">Past questions (used as inspiration only)</option>
            <option value="other">Other</option>
          </select>
          <input
            ref={docInputRef}
            type="file"
            accept=".txt,.pdf,.docx"
            onChange={handleDocUpload}
            disabled={docUploading}
            className="text-sm"
          />
        </div>

        {documents.length > 0 && (
          <div className="mt-4 flex flex-col gap-3">
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="rounded-md border border-mist px-3 py-2 text-sm"
            >
              <option value="">Select uploaded document…</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.document_type})
                </option>
              ))}
            </select>
            <select
              value={selectedTopicId}
              onChange={(e) => setSelectedTopicId(e.target.value)}
              className="rounded-md border border-mist px-3 py-2 text-sm"
            >
              <option value="">Select topic to generate for…</option>
              {topics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={1}
                max={30}
                value={genCount}
                onChange={(e) => setGenCount(Number(e.target.value))}
                className="w-20 rounded-md border border-mist px-2 py-2 text-sm"
              />
              <button
                onClick={handleGenerate}
                disabled={generating || !selectedDocId || !selectedTopicId}
                className="rounded-md bg-vital-teal px-5 py-2 text-sm font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
              >
                {generating ? "Generating…" : "Generate questions"}
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Pending review queue */}
      <section className="mt-6">
        <h2 className="font-display text-xl font-semibold text-ink-navy">
          Pending review ({pending.length})
        </h2>
        <div className="mt-4 flex flex-col gap-4">
          {pending.map((q) => (
            <div key={q.id} className="rounded-md border border-mist bg-card-bg p-5">
              <p className="font-mono text-xs uppercase tracking-widest text-graphite">
                {q.difficulty}
              </p>
              <p className="mt-1 font-medium text-ink-navy">{q.stem}</p>
              <ul className="mt-2 flex flex-col gap-1">
                {q.options.map((o) => (
                  <li
                    key={o.id}
                    className={`text-sm ${o.is_correct ? "font-medium text-vital-teal" : "text-graphite"}`}
                  >
                    {o.is_correct ? "✓ " : "  "}
                    {o.text}
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-sm text-graphite">{q.explanation}</p>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => handleApprove(q.id)}
                  className="rounded-md bg-vital-teal px-4 py-2 text-sm font-medium text-chart-cream hover:bg-ink-navy"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleReject(q.id)}
                  className="rounded-md border border-pulse-coral px-4 py-2 text-sm font-medium text-pulse-coral hover:bg-pulse-coral/10"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
          {pending.length === 0 && (
            <p className="text-graphite">Nothing pending review right now.</p>
          )}
        </div>
      </section>

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
