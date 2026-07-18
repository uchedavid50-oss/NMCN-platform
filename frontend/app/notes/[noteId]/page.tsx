"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, GeneratedQuestion } from "@/lib/api";

export default function NoteDetailPage() {
  const { noteId } = useParams<{ noteId: string }>();
  const { user, token, loading } = useRequireAuth();
  const [questions, setQuestions] = useState<GeneratedQuestion[] | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [revealedIds, setRevealedIds] = useState<Set<string>>(new Set());
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<{ question: string; reply: string }[]>([]);
  const [asking, setAsking] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !token) return;
    api
      .getGeneratedQuestions(noteId, token)
      .then(setQuestions)
      .catch(() => setQuestions([]));
  }, [user, token, noteId]);

  async function handleGenerate() {
    if (!token) return;
    setGenerating(true);
    setError(null);
    try {
      const result = await api.generateQuestionsFromNote(noteId, 5, token);
      setQuestions((prev) => [...(prev ?? []), ...result]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't generate questions right now.");
    } finally {
      setGenerating(false);
    }
  }

  function toggleReveal(id: string) {
    setRevealedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleAsk() {
    if (!token || !chatMessage.trim()) return;
    setAsking(true);
    setChatError(null);
    try {
      const result = await api.askAboutNote(noteId, chatMessage, token);
      setChatHistory((prev) => [...prev, { question: chatMessage, reply: result.reply }]);
      setChatMessage("");
    } catch (err) {
      setChatError(err instanceof ApiError ? err.message : "Couldn't get a response right now.");
    } finally {
      setAsking(false);
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
      <Link href="/notes" className="text-sm text-vital-teal hover:underline">
        ← Back to my notes
      </Link>

      <div className="mt-4 flex items-center justify-between">
        <div>
          <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
            AI-generated · private to you
          </p>
          <h1 className="mt-1 font-display text-2xl font-semibold text-ink-navy">
            Practice questions from your notes
          </h1>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="rounded-md bg-vital-teal px-5 py-2.5 text-sm font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {generating ? "Generating…" : "Generate 5 more"}
        </button>
      </div>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      <div className="mt-8 rounded-md border border-mist bg-card-bg p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
          Ask about these notes
        </p>
        <p className="mt-1 text-sm text-graphite">
          Ask anything about this specific document — the tutor answers grounded in what you
          actually uploaded.
        </p>

        {chatHistory.map((exchange, i) => (
          <div key={i} className="mt-4 border-t border-mist pt-3">
            <p className="text-sm font-medium text-ink-navy">{exchange.question}</p>
            <p className="mt-1 text-sm text-graphite">{exchange.reply}</p>
          </div>
        ))}

        {chatError && <p className="mt-3 text-sm text-pulse-coral">{chatError}</p>}

        <div className="mt-3 flex gap-2">
          <input
            type="text"
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            placeholder="Ask a question about this note…"
            disabled={asking}
            className="flex-1 rounded-md border border-mist px-3 py-2 text-sm focus:border-vital-teal focus:outline-none"
          />
          <button
            onClick={handleAsk}
            disabled={asking || !chatMessage.trim()}
            className="rounded-md border border-mist px-4 py-2 text-sm font-medium text-ink-navy transition hover:border-vital-teal disabled:opacity-50"
          >
            {asking ? "Asking…" : "Ask"}
          </button>
        </div>
      </div>

      {questions && questions.length === 0 && !generating && (
        <p className="mt-10 text-graphite">
          No questions generated yet — click &quot;Generate 5 more&quot; to create some from this
          note.
        </p>
      )}

      <div className="mt-8 flex flex-col gap-4">
        {questions?.map((q, i) => {
          const revealed = revealedIds.has(q.id);
          const correctOption = q.options.find((o) => o.is_correct);
          return (
            <button
              key={q.id}
              onClick={() => toggleReveal(q.id)}
              className="rounded-md border border-mist bg-card-bg p-5 text-left transition hover:border-vital-teal"
            >
              <p className="font-mono text-xs uppercase tracking-widest text-graphite">
                Question {i + 1} · {q.difficulty}
              </p>
              <p className="mt-1 font-body font-medium text-ink-navy">{q.stem}</p>

              {revealed && (
                <div className="mt-3 border-t border-mist pt-3">
                  <p className="text-sm text-vital-teal">Answer: {correctOption?.text}</p>
                  <p className="mt-1 text-sm text-graphite">{q.explanation}</p>
                </div>
              )}
              <p className="mt-3 font-mono text-xs uppercase tracking-widest text-vital-teal">
                {revealed ? "Click to hide" : "Click to reveal answer"}
              </p>
            </button>
          );
        })}
      </div>
    </main>
  );
}
