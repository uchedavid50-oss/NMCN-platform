"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, MockSubmitResponse, PracticeQuestion } from "@/lib/api";

type Phase = "loading" | "exam" | "summary" | "error";

const MOCK_DURATION_MINUTES = 30;

function parseUtcDate(isoString: string): Date {
  // The backend sends naive UTC timestamps (no timezone suffix). Without an
  // explicit "Z", the browser would interpret them as local time, which is
  // wrong for anyone not in UTC+0 and silently breaks the countdown.
  return new Date(isoString.endsWith("Z") ? isoString : `${isoString}Z`);
}

function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export default function MockExamPage() {
  const { topicId } = useParams<{ topicId: string }>();
  const { user, token, loading } = useRequireAuth();

  const [phase, setPhase] = useState<Phase>("loading");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<PracticeQuestion[]>([]);
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [autoSubmitted, setAutoSubmitted] = useState(false);
  const [summary, setSummary] = useState<MockSubmitResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const hasSubmittedRef = useRef(false);

  const handleSubmit = useCallback(
    async (auto = false) => {
      if (!attemptId || !token || hasSubmittedRef.current) return;
      hasSubmittedRef.current = true;
      setSubmitting(true);
      try {
        const result = await api.submitMockExam(attemptId, token);
        setSummary(result);
        setAutoSubmitted(auto);
        setPhase("summary");
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : "Couldn't submit the exam.");
        setPhase("error");
      } finally {
        setSubmitting(false);
      }
    },
    [attemptId, token]
  );

  useEffect(() => {
    if (!user || !token) return;
    api
      .startMock(topicId, MOCK_DURATION_MINUTES, token)
      .then((res) => {
        if (res.questions.length === 0) {
          setErrorMsg("This topic doesn't have any questions yet.");
          setPhase("error");
          return;
        }
        setAttemptId(res.attempt_id);
        setQuestions(res.questions);
        setExpiresAt(parseUtcDate(res.expires_at));
        setPhase("exam");
      })
      .catch((err) => {
        setErrorMsg(err instanceof Error ? err.message : "Couldn't start this mock exam.");
        setPhase("error");
      });
  }, [user, token, topicId]);

  useEffect(() => {
    if (phase !== "exam" || !expiresAt) return;
    const tick = () => {
      const remaining = Math.max(0, Math.floor((expiresAt.getTime() - Date.now()) / 1000));
      setTimeLeft(remaining);
      if (remaining <= 0) {
        handleSubmit(true);
      }
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [phase, expiresAt, handleSubmit]);

  if (loading || !user || phase === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-pulse-coral">{errorMsg}</p>
        <Link href="/subjects" className="mt-4 inline-block text-vital-teal hover:underline">
          ← Back to subjects
        </Link>
      </main>
    );
  }

  if (phase === "summary" && summary) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        {autoSubmitted && (
          <p className="mb-6 rounded-md border border-pulse-coral bg-pulse-coral/10 px-4 py-3 text-sm text-pulse-coral">
            Time&apos;s up — your exam was submitted automatically.
          </p>
        )}
        <p className="text-center font-mono text-sm uppercase tracking-widest text-vital-teal">
          Mock exam complete
        </p>
        <p className="mt-4 text-center font-display text-6xl font-semibold text-ink-navy">
          {summary.score_percentage}%
        </p>
        <p className="mt-2 text-center text-graphite">
          {summary.correct_answers} of {summary.total_questions} correct
        </p>

        <div className="mt-10 flex flex-col gap-4">
          {summary.breakdown.map((item, i) => (
            <div
              key={item.question_id}
              className={`rounded-md border p-5 ${
                item.is_correct ? "border-mist" : "border-pulse-coral/40"
              }`}
            >
              <p className="font-mono text-xs uppercase tracking-widest text-graphite">
                Question {i + 1}
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
          href="/subjects"
          className="mt-8 inline-block rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
        >
          Back to subjects
        </Link>
      </main>
    );
  }

  const question = questions[currentIndex];
  const selectedOptionId = answers[question.id];
  const isLastQuestion = currentIndex === questions.length - 1;
  const lowOnTime = timeLeft <= 60;

  async function handleSelectOption(optionId: string) {
    if (!attemptId || !token) return;
    setAnswers((prev) => ({ ...prev, [question.id]: optionId }));
    try {
      await api.submitMockAnswer(attemptId, question.id, optionId, token);
    } catch {
      // Best-effort: local selection still reflects the student's choice even if
      // the sync call fails; the next selection or the final submit will retry.
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <div className="flex items-center justify-between">
        <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
          Question {currentIndex + 1} of {questions.length}
        </p>
        <p className={`font-mono text-lg ${lowOnTime ? "text-pulse-coral" : "text-ink-navy"}`}>
          {formatTime(timeLeft)}
        </p>
      </div>

      <div className="mt-4 flex gap-2">
        {questions.map((q, i) => (
          <button
            key={q.id}
            onClick={() => setCurrentIndex(i)}
            className={`h-2 flex-1 rounded-full transition ${
              i === currentIndex
                ? "bg-ink-navy"
                : answers[q.id]
                ? "bg-vital-teal"
                : "bg-mist"
            }`}
            aria-label={`Go to question ${i + 1}`}
          />
        ))}
      </div>

      <h1 className="mt-6 font-display text-2xl font-semibold text-ink-navy">{question.stem}</h1>

      <div className="mt-6 flex flex-col gap-3">
        {question.options.map((option) => (
          <button
            key={option.id}
            onClick={() => handleSelectOption(option.id)}
            className={`rounded-md border px-5 py-4 text-left font-body text-lg text-ink-navy transition ${
              option.id === selectedOptionId
                ? "border-vital-teal bg-vital-teal/10"
                : "border-mist hover:border-vital-teal hover:bg-white"
            }`}
          >
            {option.text}
          </button>
        ))}
      </div>

      <div className="mt-8 flex items-center justify-between">
        <button
          onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
          disabled={currentIndex === 0}
          className="rounded-md border border-mist px-5 py-2.5 font-medium text-ink-navy disabled:opacity-40"
        >
          Previous
        </button>

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
            onClick={() => setCurrentIndex((i) => Math.min(questions.length - 1, i + 1))}
            className="rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy"
          >
            Next
          </button>
        )}
      </div>

      <button
        onClick={() => handleSubmit(false)}
        disabled={submitting || isLastQuestion}
        className="mt-4 text-sm text-graphite underline hover:text-pulse-coral disabled:hidden"
      >
        Submit exam now
      </button>
    </main>
  );
}
