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
import { approveAllPending } from "@/lib/api-extras-5";
import { generateTopicNote } from "@/lib/api-extras-7";
import { getTopicVideo, setTopicVideo } from "@/lib/api-extras-8";

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
  const [extractionMode, setExtractionMode] = useState("ai_generate");
  const [generating, setGenerating] = useState(false);
 const [bulkTarget, setBulkTarget] = useState(100);
const [bulkProgress, setBulkProgress] = useState(0);
const [bulkRunning, setBulkRunning] = useState(false);
const [bulkStatus, setBulkStatus] = useState("");
const [useDocument, setUseDocument] = useState(true);
const [bulkScope, setBulkScope] = useState("single"); // "single" | "all_topics"
const [noteGenerating, setNoteGenerating] = useState(false);
const [noteBulkRunning, setNoteBulkRunning] = useState(false);
const [noteBulkProgress, setNoteBulkProgress] = useState(0);
const [noteBulkStatus, setNoteBulkStatus] = useState("");
  const [bulkApproving, setBulkApproving] = useState(false);
  const [bulkMessage, setBulkMessage] = useState<string | null>(null);
  const [approveProgress, setApproveProgress] = useState(0);
  const [approveTotal, setApproveTotal] = useState(0);
  const [videoUrl, setVideoUrl] = useState("");
  const [videoSaving, setVideoSaving] = useState(false);
  const [videoMessage, setVideoMessage] = useState<string | null>(null);

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

  useEffect(() => {
    if (!token || !selectedTopicId) {
      setVideoUrl("");
      return;
    }
    getTopicVideo(selectedTopicId, token)
      .then((v) => setVideoUrl(v.youtube_url))
      .catch(() => setVideoUrl(""));
  }, [token, selectedTopicId]);

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
      await api.generatePendingQuestions(selectedDocId, selectedTopicId, genCount, token, extractionMode);
      refreshAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Generation failed.");
    } finally {
      setGenerating(false);
    }
  }
async function generateForOneTopic(topicId: string, target: number, docId: string | null) {
  const batchSize = 30;
  let totalCreated = 0;
  let consecutiveFailures = 0;
  while (totalCreated < target) {
    const remaining = target - totalCreated;
    const thisBatch = Math.min(batchSize, remaining);
    try {
      const result = await api.generatePendingQuestions(
        docId,
        topicId,
        thisBatch,
        token!,
        extractionMode
      );
      totalCreated += result.length;
      consecutiveFailures = 0;
      if (result.length === 0) break;
    } catch (err) {
      consecutiveFailures += 1;
      if (consecutiveFailures >= 2) break;
      // wait before retrying, so a rate limit or hiccup doesn't turn into rapid-fire hammering
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
  }
  return totalCreated;
}

  async function handleBulkGenerate() {
    if (!token) return;
    if (useDocument && !selectedDocId) return;
    if (bulkScope === "single" && !selectedTopicId) return;

    setBulkRunning(true);
    setBulkProgress(0);
    setError(null);
    const docId = useDocument ? selectedDocId : null;

    try {
      if (bulkScope === "single") {
        setBulkStatus(topics.find((t) => t.id === selectedTopicId)?.name || "");
        const created = await generateForOneTopic(selectedTopicId, bulkTarget, docId);
        setBulkProgress(created);
       } else {
        let grandTotal = 0;
        for (const topic of topics) {
          setBulkStatus(topic.name);
          const created = await generateForOneTopic(topic.id, bulkTarget, docId);
          grandTotal += created;
          setBulkProgress(grandTotal);
          await new Promise((resolve) => setTimeout(resolve, 500));
        }
      }
      refreshAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Bulk generation failed.");
    } finally {
      setBulkRunning(false);
      setBulkStatus("");
    }
  }

async function handleGenerateNote() {
    if (!token || !selectedTopicId) return;
    setNoteGenerating(true);
    setError(null);
    try {
      await generateTopicNote(selectedTopicId, token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Note generation failed.");
    } finally {
      setNoteGenerating(false);
    }
  }

  async function handleSaveVideo() {
    if (!token || !selectedTopicId || !videoUrl.trim()) return;
    setVideoSaving(true);
    setVideoMessage(null);
    setError(null);
    try {
      await setTopicVideo(selectedTopicId, videoUrl.trim(), token);
      setVideoMessage("Video saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save the video.");
    } finally {
      setVideoSaving(false);
    }
  }

  async function handleBulkGenerateNotes() {
  if (!token) return;
  setNoteBulkRunning(true);
  setNoteBulkProgress(0);
  setError(null);
  let done = 0;
  let consecutiveFailures = 0;
  try {
    for (const topic of topics) {
      setNoteBulkStatus(topic.name);
      try {
        await generateTopicNote(topic.id, token);
        consecutiveFailures = 0;
      } catch {
        consecutiveFailures += 1;
        if (consecutiveFailures >= 3) break; // stop if AI seems to be consistently failing
      }
      done += 1;
      setNoteBulkProgress(done);
    }
  } finally {
    setNoteBulkRunning(false);
    setNoteBulkStatus("");
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

  async function handleApproveAll() {
    if (!token || pending.length === 0) return;
    const total = pending.length;
    const confirmed = window.confirm(
      `Approve all ${total} pending question(s) without reviewing them individually? This publishes them straight to the official bank.`
    );
    if (!confirmed) return;

    setBulkApproving(true);
    setApproveProgress(0);
    setApproveTotal(total);
    setBulkMessage(null);
    setError(null);

    // Batched like bulk-generate: one huge request/transaction for 1000+
    // pending questions was slow enough to look hung to the caller, with
    // no feedback in the meantime. Chunking also means a failure partway
    // through doesn't lose progress already committed.
    let approvedSoFar = 0;
    try {
      let remaining = total;
      while (remaining > 0) {
        const result = await approveAllPending(token, undefined, 200);
        approvedSoFar += result.approved_count;
        remaining = result.remaining_count;
        setApproveProgress(approvedSoFar);
        if (result.approved_count === 0) break; // nothing left this call could approve; avoid spinning forever
      }
      setBulkMessage(`Approved ${approvedSoFar} question(s).`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Bulk approve failed.");
      setBulkMessage(approvedSoFar > 0 ? `Approved ${approvedSoFar} question(s) before the error.` : null);
    } finally {
      setBulkApproving(false);
      refreshAll();
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
              <select
                value={extractionMode}
                onChange={(e) => setExtractionMode(e.target.value)}
                className="rounded-md border border-mist px-2 py-2 text-sm"
              >
                <option value="ai_generate">AI generate (new questions)</option>
                <option value="verbatim">Copy verbatim (exact + rationale)</option>
              </select>
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

            <div className="mt-4 flex flex-col gap-3 border-t border-mist pt-4">
                <div className="flex items-center gap-4 text-sm text-graphite">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      checked={useDocument}
                      onChange={() => setUseDocument(true)}
                    />
                    Use uploaded document
                  </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    checked={!useDocument}
                    onChange={() => setUseDocument(false)}
                  />
                  AI knowledge only (no document)
                </label>
              </div>

              <div className="flex items-center gap-4 text-sm text-graphite">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    checked={bulkScope === "single"}
                    onChange={() => setBulkScope("single")}
                  />
                  Selected topic only
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    checked={bulkScope === "all_topics"}
                    onChange={() => setBulkScope("all_topics")}
                  />
                  All topics ({topics.length})
                </label>
              </div>

              <div className="flex items-center gap-2">
                <label className="text-sm text-graphite">Target per topic:</label>
                <input
                  type="number"
                  min={1}
                  max={2000}
                  value={bulkTarget}
                  onChange={(e) => setBulkTarget(Number(e.target.value))}
                  className="w-24 rounded-md border border-mist px-2 py-2 text-sm"
                />
                <button
                  onClick={handleBulkGenerate}
                  disabled={
                    bulkRunning ||
                    (useDocument && !selectedDocId) ||
                    (bulkScope === "single" && !selectedTopicId)
                  }
                  className="rounded-md border border-vital-teal px-5 py-2 text-sm font-medium text-vital-teal transition hover:bg-vital-teal/10 disabled:opacity-50"
                >
                  {bulkRunning
                    ? `Generating "${bulkStatus}"… (${bulkProgress} total)`
                    : `Bulk generate`}
                </button>
              </div>
            </div>
            </div>
        )}
      </section>
{/* Study notes generation */}
      <section className="mt-6 rounded-md border border-mist bg-card-bg p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
          Generate study notes (per topic, replaces existing note)
        </p>
        <p className="mt-1 text-sm text-graphite">
          Uses AI knowledge only, no document needed. Select a topic above first for a single note,
          or generate for every topic at once below.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <button
            onClick={handleGenerateNote}
            disabled={noteGenerating || !selectedTopicId}
            className="rounded-md bg-vital-teal px-5 py-2 text-sm font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
          >
            {noteGenerating ? "Generating…" : "Generate note for selected topic"}
          </button>
          <button
            onClick={handleBulkGenerateNotes}
            disabled={noteBulkRunning}
            className="rounded-md border border-vital-teal px-5 py-2 text-sm font-medium text-vital-teal transition hover:bg-vital-teal/10 disabled:opacity-50"
          >
            {noteBulkRunning
              ? `Generating "${noteBulkStatus}"… (${noteBulkProgress}/${topics.length})`
              : `Generate notes for all topics (${topics.length})`}
          </button>
        </div>
      </section>
      {/* OSCE demonstration video */}
      <section className="mt-6 rounded-md border border-mist bg-card-bg p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
          OSCE demonstration video (per topic)
        </p>
        <p className="mt-1 text-sm text-graphite">
          Select a topic above, paste a YouTube URL, and save. Shown to students on that
          procedure&apos;s OSCE page before the practice questions.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <input
            type="url"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            disabled={!selectedTopicId}
            className="min-w-[20rem] flex-1 rounded-md border border-mist px-3 py-2 text-sm disabled:opacity-50"
          />
          <button
            onClick={handleSaveVideo}
            disabled={videoSaving || !selectedTopicId || !videoUrl.trim()}
            className="rounded-md bg-vital-teal px-5 py-2 text-sm font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
          >
            {videoSaving ? "Saving…" : "Save video"}
          </button>
        </div>
        {videoMessage && <p className="mt-2 text-sm text-vital-teal">{videoMessage}</p>}
      </section>
      {/* Pending review queue */}
      <section className="mt-6">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-xl font-semibold text-ink-navy">
            Pending review ({pending.length})
          </h2>
          {pending.length > 0 && (
            <button
              onClick={handleApproveAll}
              disabled={bulkApproving}
              className="rounded-md bg-vital-teal px-4 py-2 text-sm font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
            >
              {bulkApproving ? `Approving… (${approveProgress}/${approveTotal})` : `✅ Approve all ${pending.length}`}
            </button>
          )}
        </div>
        {bulkMessage && <p className="mt-2 text-sm text-vital-teal">{bulkMessage}</p>}
        <p className="mt-1 text-xs text-graphite">
          Bulk-approving skips individual review — use once you trust the pattern from a few
          spot-checked batches, not as a default.
        </p>
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
