"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, CBTExamStartResponse, CBTExamSubmitResponse } from "@/lib/api";

type Phase = "loading" | "exam" | "summary" | "error";

function parseUtcDate(isoString: string): Date {
  return new Date(isoString.endsWith("Z") ? isoString : `${isoString}Z`);
}

function formatDuration(totalSeconds: number) {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export default function CBTExamPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { user, token, loading } = useRequireAuth();

  const [phase, setPhase] = useState<Phase>("loading");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [session, setSession] = useState<CBTExamStartResponse | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [jumpValue, setJumpValue] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [autoSubmitted, setAutoSubmitted] = useState(false);
  const [summary, setSummary] = useState<CBTExamSubmitResponse | null>(null);
  const hasSubmittedRef = useRef(false);

  useEffect(() => {
    const stored = sessionStorage.getItem(`cbt-exam-${sessionId}`);
    if (!stored) {
      setErrorMsg(
        "Couldn't find this exam's questions — this can happen after a page refresh. Start a new exam from the CBT Center."
      );
      setPhase("error");
      return;
    }
    const parsed: CBTExamStartResponse = JSON.parse(stored);
    setSession(parsed);
    setPhase("exam");
  }, [sessionId]);

  const handleSubmit = useCallback(
    async (auto = false) => {
      if (!token || hasSubmittedRef.current) return;
      hasSubmittedRef.current = true;
      setSubmitting(true);
      try {
        const result = await api.submitCBTExam(sessionId, token);
        setSummary(result);
        setAutoSubmitted(auto);
        setPhase("summary");
        sessionStorage.removeItem(`cbt-exam-${sessionId}`);
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : "Couldn't submit the exam.");
        setPhase("error");
      } finally {
        setSubmitting(false);
      }
    },
    [sessionId, token]
  );

  useEffect(() => {
    if (phase !== "exam" || !session) return;
    const expiresAt = parseUtcDate(session.expires_at);
    const tick = () => {
      const remaining = Math.max(0, Math.floor((expiresAt.getTime() - Date.now()) / 1000));
      setTimeLeft(remaining);
      if (remaining <= 0) handleSubmit(true);
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [phase, session, handleSubmit]);

  async function handleSelect(questionId: string, optionId: string) {
    if (!token) return;
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
    try {
      await api.submitCBTExamAnswer(sessionId, questionId, optionId, token);
    } catch {
      // Best-effort — local selection still reflects the choice even if sync fails.
    }
  }

  function handleJump() {
    const num = parseInt(jumpValue, 10);
    if (session && num >= 1 && num <= session.questions.length) {
      setCurrentIndex(num - 1);
    }
    setJumpValue("");
  }

  if (loading || !user || phase === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="mx-auto max-w-xl px-6 py-16 text-center">
        <p className="text-pulse-coral">{errorMsg}</p>
        <Link href="/cbt-exam" className="mt-4 inline-block text-vital-teal hover:underline">
          ← Back to CBT Center
        </Link>
      </main>
    );
  }

  if (phase === "summary" && summary) {
    const answeredCount = Object.keys(answers).length;
    return (
      <main className="mx-auto max-w-3xl px-6 py-16">
        {autoSubmitted && (
          <p className="mb-6 rounded-md border border-pulse-coral bg-pulse-coral/10 px-4 py-3 text-sm text-pulse-coral">
            Time&apos;s up — your exam was submitted automatically.
          </p>
        )}
        <p className="text-center font-mono text-sm uppercase tracking-widest text-vital-teal">
          Full exam simulation complete
        </p>
        <p className="mt-4 text-center font-display text-6xl font-semibold text-ink-navy">
          {summary.score_percentage}%
        </p>
        <p className="mt-2 text-center text-graphite">
          {summary.correct_answers} of {summary.total_questions} correct · {answeredCount} answered
        </p>

        <div className="mt-10 flex flex-col gap-4">
          {summary.breakdown.map((item, i) => (
            <div
              key={item.question_id}
              className={`rounded-md border p-5 ${item.is_correct ? "border-mist" : "border-pulse-coral/40"}`}
            >
              <p className="font-mono text-xs uppercase tracking-widest text-graphite">
                Question {i + 1} · {item.subject_name}
              </p>
              <p className="mt-1 font-body font-medium text-ink-navy">{item.stem}</p>
              <p className="mt-3 text-sm">
                <span className="text-graphite">Your answer: </span>
                <span className={item.is_correct ? "text-vital-teal" : "text-pulse-coral"}>
                  {item.your_answer_text ?? "Not answered"}
                </span>
              </p>
              {!item.is_correct && (
                <p className="text-sm">
                  <span className="text-graphite">Correct answer: </span>
                  <span className="text-vital-teal">{item.correct_option_text}</span>
                </p>
              )}
              <p className="mt-2 text-sm text-graphite">{item.explanation}</p>
            </div>
          ))}
        </div>

        <Link
          href="/dashboard"
          className="mt-8 inline-block rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
        >
          Back to dashboard
        </Link>
      </main>
    );
  }

  if (!session) return null;

  const question = session.questions[currentIndex];
  const selectedOptionId = answers[question.id];
  const isLastQuestion = currentIndex === session.questions.length - 1;
  const answeredCount = Object.keys(answers).length;
  const lowOnTime = timeLeft <= 300; // under 5 minutes

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <div className="flex items-center justify-between">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
          Question {currentIndex + 1} of {session.questions.length} · {answeredCount} answered
        </p>
        <p className={`font-mono text-lg ${lowOnTime ? "text-pulse-coral" : "text-ink-navy"}`}>
          {formatDuration(timeLeft)}
        </p>
      </div>

      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-mist">
        <div
          className="h-full rounded-full bg-vital-teal"
          style={{ width: `${(answeredCount / session.questions.length) * 100}%` }}
        />
      </div>

      <h1 className="mt-6 font-display text-2xl font-semibold text-ink-navy">{question.stem}</h1>

      <div className="mt-6 flex flex-col gap-3">
        {question.options.map((option) => (
          <button
            key={option.id}
            onClick={() => handleSelect(question.id, option.id)}
            className={`rounded-md border px-5 py-3 text-left font-body text-ink-navy transition ${
              option.id === selectedOptionId
                ? "border-vital-teal bg-vital-teal/10"
                : "border-mist hover:border-vital-teal"
            }`}
          >
            {option.text}
          </button>
        ))}
      </div>

      <div className="mt-8 flex items-center justify-between gap-3">
        <button
          onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
          disabled={currentIndex === 0}
          className="rounded-md border border-mist px-5 py-2.5 font-medium text-ink-navy disabled:opacity-40"
        >
          Previous
        </button>

        <div className="flex items-center gap-2">
          <input
            type="number"
            min={1}
            max={session.questions.length}
            value={jumpValue}
            onChange={(e) => setJumpValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleJump()}
            placeholder="Go to #"
            className="w-20 rounded-md border border-mist px-2 py-2 text-center text-sm focus:border-vital-teal focus:outline-none"
          />
          <button
            onClick={handleJump}
            className="rounded-md border border-mist px-3 py-2 text-sm font-medium text-ink-navy hover:border-vital-teal"
          >
            Go
          </button>
        </div>

        {isLastQuestion ? (
          <button
            onClick={() => handleSubmit(false)}
            disabled={submitting}
            className="rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
          >
            {submitting ? "Submitting…" : "Submit exam"}
          </button>
        ) : (
          <button
            onClick={() => setCurrentIndex((i) => Math.min(session.questions.length - 1, i + 1))}
            className="rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy"
          >
            Next
          </button>
        )}
      </div>

      <button
        onClick={() => handleSubmit(false)}
        disabled={submitting}
        className="mt-4 text-sm text-graphite underline hover:text-pulse-coral"
      >
        Submit exam now
      </button>
    </main>
  );
}
