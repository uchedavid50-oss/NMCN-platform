"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, Topic } from "@/lib/api";
import {
  listTextbookFolders,
  createTextbookFolder,
  listTextbooksInFolder,
  uploadTextbook,
  deleteTextbook,
  downloadTextbook,
  generateQuestionsFromTextbook,
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

  // Question generation state
  const [topics, setTopics] = useState<Topic[]>([]);
  const [genTextbookId, setGenTextbookId] = useState<string | null>(null);
  const [genTopicId, setGenTopicId] = useState("");
  const [genTargetTotal, setGenTargetTotal] = useState(250);
  const [genDistributeAll, setGenDistributeAll] = useState(false);
  const [genRunning, setGenRunning] = useState(false);
  const [genProgress, setGenProgress] = useState(0);
  const [genCurrentTopic, setGenCurrentTopic] = useState<string | null>(null);
  const [genMessage, setGenMessage] = useState<string | null>(null);

  function refreshFolders() {
    if (!token) return;
    listTextbookFolders(token).then(setFolders).catch(() => {});
  }

  useEffect(() => {
    if (!user || !token) return;
    refreshFolders();
    if (user.role === "admin") {
      api.listAllTopics().then(setTopics).catch(() => {});
    }
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

  async function handleDownload(id: string, filename: string) {
    if (!token) return;
    try {
      await downloadTextbook(id, filename, token);
    } catch {
      setError("Couldn't download this file.");
    }
  }

  async function handleGenerate(textbookId: string) {
    if (!token) return;
    if (!genDistributeAll && !genTopicId) return;
    if (genDistributeAll && topics.length === 0) return;

    setGenRunning(true);
    setGenProgress(0);
    setGenMessage(null);
    setError(null);

    const BATCH_SIZE = 20;
    let totalGenerated = 0;

    // Single-topic mode: everything goes to the one topic you picked.
    // Distribute-all mode: the target total is split evenly across every
    // existing topic, so one document (e.g. a full year's exam covering
    // every subject) can seed practice content everywhere in one run.
    const topicsToUse = genDistributeAll ? topics : topics.filter((t) => t.id === genTopicId);
    const perTopicTarget = Math.max(1, Math.round(genTargetTotal / topicsToUse.length));

    try {
      for (const topic of topicsToUse) {
        setGenCurrentTopic(topic.name);
        let topicGenerated = 0;
        while (topicGenerated < perTopicTarget) {
          const remaining = perTopicTarget - topicGenerated;
          const batchCount = Math.min(BATCH_SIZE, remaining);
          const result = await generateQuestionsFromTextbook(textbookId, topic.id, batchCount, token);
          topicGenerated += result.length;
          totalGenerated += result.length;
          setGenProgress(totalGenerated);
          await new Promise((resolve) => setTimeout(resolve, 1500));
        }
      }
      setGenMessage(
        `Generated ${totalGenerated} question(s) across ${topicsToUse.length} topic(s), into the pending review queue. Go to Admin: Content to approve them.`
      );
    } catch (err) {
      setGenMessage(
        `Stopped after ${totalGenerated} question(s) (last working on "${genCurrentTopic}") — ${
          err instanceof ApiError ? err.message : "an error occurred"
        }. You can start again to keep going.`
      );
    } finally {
      setGenRunning(false);
      setGenCurrentTopic(null);
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
        Browse and download nursing textbooks &amp; past questions
      </h1>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      {user.role === "admin" && (
        <div className="mt-6 rounded-md border border-mist bg-card-bg p-5">
          <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
            Admin: create a folder
          </p>
          <p className="mt-1 text-xs text-graphite">
            For past exam papers, name the folder something like &quot;Past Questions - Anatomy&quot;.
          </p>
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Folder name (e.g. Past Questions - Anatomy)"
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

          <div className="flex flex-col gap-3">
            {textbooks.map((t) => (
              <div key={t.id} className="rounded-md border border-mist px-4 py-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-ink-navy">{t.title}</p>
                    <p className="text-xs text-graphite">
                      {(t.file_size / 1024 / 1024).toFixed(1)} MB
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleDownload(t.id, t.filename)}
                      className="rounded-md bg-vital-teal px-4 py-2 text-sm font-medium text-chart-cream hover:bg-ink-navy"
                    >
                      View / Download
                    </button>
                    {user.role === "admin" && (
                      <>
                        <button
                          onClick={() => setGenTextbookId(genTextbookId === t.id ? null : t.id)}
                          className="rounded-md border border-vital-teal px-3 py-2 text-sm font-medium text-vital-teal hover:bg-vital-teal/10"
                        >
                          🤖 Generate
                        </button>
                        <button
                          onClick={() => handleDelete(t.id)}
                          className="text-sm text-pulse-coral hover:underline"
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {genTextbookId === t.id && (
                  <div className="mt-3 rounded-md border border-mist bg-card-bg p-4">
                    <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
                      Generate practice questions from this document
                    </p>
                    <p className="mt-1 text-xs text-graphite">
                      Never copies verbatim — writes new questions inspired by the same concepts.
                      Everything lands in the pending review queue first.
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <input
                        type="checkbox"
                        id={`distribute-${t.id}`}
                        checked={genDistributeAll}
                        onChange={(e) => setGenDistributeAll(e.target.checked)}
                      />
                      <label htmlFor={`distribute-${t.id}`} className="text-sm text-ink-navy">
                        Distribute across every subject/topic automatically ({topics.length}{" "}
                        topics found)
                      </label>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      {!genDistributeAll && (
                        <select
                          value={genTopicId}
                          onChange={(e) => setGenTopicId(e.target.value)}
                          className="rounded-md border border-mist px-3 py-2 text-sm"
                        >
                          <option value="">Select topic…</option>
                          {topics.map((topic) => (
                            <option key={topic.id} value={topic.id}>
                              {topic.name}
                            </option>
                          ))}
                        </select>
                      )}
                      <label className="flex items-center gap-2 text-sm text-graphite">
                        Total to generate:
                        <input
                          type="number"
                          min={1}
                          max={5000}
                          value={genTargetTotal}
                          onChange={(e) => setGenTargetTotal(Number(e.target.value))}
                          className="w-24 rounded-md border border-mist px-2 py-2 text-sm"
                        />
                      </label>
                      <button
                        onClick={() => handleGenerate(t.id)}
                        disabled={genRunning || (!genDistributeAll && !genTopicId)}
                        className="rounded-md bg-vital-teal px-4 py-2 text-sm font-medium text-chart-cream hover:bg-ink-navy disabled:opacity-50"
                      >
                        {genRunning
                          ? `Generating… (${genProgress}/${genTargetTotal}${
                              genCurrentTopic ? ` · ${genCurrentTopic}` : ""
                            })`
                          : "Start"}
                      </button>
                    </div>
                    {genDistributeAll && (
                      <p className="mt-2 text-xs text-graphite">
                        ~{Math.max(1, Math.round(genTargetTotal / Math.max(1, topics.length)))}{" "}
                        question(s) per topic, across all {topics.length} topics.
                      </p>
                    )}
                    {genMessage && (
                      <p className="mt-2 text-sm text-graphite">{genMessage}</p>
                    )}
                    <p className="mt-2 text-xs text-graphite">
                      Large totals run as several smaller batches automatically — this can take a
                      while for big numbers. You can leave this page open and check back.
                    </p>
                  </div>
                )}
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
