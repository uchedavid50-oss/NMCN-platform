"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { getEntranceExamQuestions, EntranceExamQuestion } from "@/lib/api-extras-10";

export default function EntranceExamSubjectPage() {
  const { subject: rawSubject } = useParams<{ subject: string }>();
  const subject = decodeURIComponent(rawSubject);
  const { user, token, loading } = useRequireAuth();

  const [questions, setQuestions] = useState<EntranceExamQuestion[] | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [attemptText, setAttemptText] = useState("");
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    if (!user || !token) return;
    getEntranceExamQuestions(subject, 10, token)
      .then(setQuestions)
      .catch(() => setQuestions([]));
  }, [user, token, subject]);

  function goTo(index: number) {
    setCurrentIndex(index);
    setAttemptText("");
    setRevealed(false);
  }

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  const question = questions?.[currentIndex];

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
        Nursing Entrance Exams
      </p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">{subject}</h1>

      {questions && questions.length === 0 && (
        <div className="mt-8 rounded-md border border-mist bg-card-bg p-6 text-center">
          <p className="text-graphite">Questions for this subject are being prepared. Check back soon!</p>
        </div>
      )}

      {question && (
        <>
          <p className="mt-8 font-mono text-sm text-graphite">
            Question {currentIndex + 1} of {questions?.length}
            <span className="ml-2 uppercase tracking-widest text-vital-teal">
              {question.question_type.replace("_", " ")}
            </span>
          </p>
          <p className="mt-3 font-display text-xl font-semibold text-ink-navy">
            {question.question_text}
          </p>

          {!revealed && (
            <>
              <textarea
                value={attemptText}
                onChange={(e) => setAttemptText(e.target.value)}
                placeholder="Write your answer here before revealing the correct one…"
                rows={4}
                className="mt-4 w-full rounded-md border border-mist px-4 py-3 text-sm"
              />
              <button
                onClick={() => setRevealed(true)}
                className="mt-4 rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
              >
                Show answer
              </button>
            </>
          )}

          {revealed && (
            <div className="animate-fade-in-up mt-4 rounded-md border border-mist bg-card-bg p-5">
              <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
                Model answer
              </p>
              <p className="mt-1 text-ink-navy">{question.model_answer}</p>
              <p className="mt-3 font-mono text-xs uppercase tracking-widest text-vital-teal">
                Explanation
              </p>
              <p className="mt-1 text-graphite">{question.explanation}</p>
            </div>
          )}

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={() => goTo(Math.max(0, currentIndex - 1))}
              disabled={currentIndex === 0}
              className="rounded-md border border-mist px-4 py-2 text-sm font-medium text-ink-navy transition hover:border-vital-teal disabled:opacity-50"
            >
              ← Previous
            </button>
            <button
              onClick={() => goTo(Math.min((questions?.length || 1) - 1, currentIndex + 1))}
              disabled={!questions || currentIndex >= questions.length - 1}
              className="rounded-md border border-mist px-4 py-2 text-sm font-medium text-ink-navy transition hover:border-vital-teal disabled:opacity-50"
            >
              Next →
            </button>
          </div>
        </>
      )}

      <div className="mt-10">
        <Link href="/entrance-exam" className="text-sm text-vital-teal hover:underline">
          ← Back to subjects
        </Link>
      </div>
    </main>
  );
}
