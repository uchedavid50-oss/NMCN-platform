"use client";

import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ENTRANCE_EXAM_SUBJECTS } from "@/lib/api-extras-10";

export default function EntranceExamPage() {
  const { user, loading } = useRequireAuth();

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
        Nursing Entrance Exams
      </p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Past question bank
      </h1>
      <p className="mt-3 text-graphite">
        Pick a subject to practice short-answer, fill-in-the-blank, and theory-style questions
        in the format of the nursing school entrance exam.
      </p>

      <div className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {ENTRANCE_EXAM_SUBJECTS.map((subject) => (
          <Link
            key={subject}
            href={`/entrance-exam/${encodeURIComponent(subject)}`}
            className="rounded-md border border-mist bg-card-bg px-6 py-5 text-center font-display text-lg font-semibold text-ink-navy transition hover:border-vital-teal"
          >
            {subject}
          </Link>
        ))}
      </div>

      <Link href="/dashboard" className="mt-10 inline-block text-sm text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
