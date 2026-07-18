"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, Topic } from "@/lib/api";

export default function SubjectTopicsPage() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const { user, loading } = useRequireAuth();
  const [topics, setTopics] = useState<Topic[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api
      .listTopics(subjectId)
      .then(setTopics)
      .catch(() => setError("Couldn't load topics. Try refreshing."));
  }, [user, subjectId]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <Link href="/subjects" className="text-sm text-vital-teal hover:underline">
        ← Back to subjects
      </Link>
      <p className="mt-4 font-mono text-sm uppercase tracking-widest text-vital-teal">Topics</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Choose a topic
      </h1>

      {error && <p className="mt-6 text-pulse-coral">{error}</p>}

      {topics && topics.length === 0 && (
        <p className="mt-6 text-graphite">
          No topics have been added to this subject yet — check back soon.
        </p>
      )}

      <div className="mt-8 flex flex-col gap-3">
        {topics?.map((topic) => (
          <div
            key={topic.id}
            className="flex items-center justify-between rounded-md border border-mist px-5 py-4"
          >
            <span className="font-body text-lg text-ink-navy">{topic.name}</span>
            <div className="flex gap-2">
              <Link
                href={`/flashcards/${topic.id}`}
                className="rounded-md border border-mist px-4 py-2 text-sm font-medium text-ink-navy transition hover:border-vital-teal"
              >
                Flashcards
              </Link>
              <Link
                href={`/practice/${topic.id}`}
                className="rounded-md border border-mist px-4 py-2 text-sm font-medium text-ink-navy transition hover:border-vital-teal"
              >
                Practice
              </Link>
              <Link
                href={`/mock/${topic.id}`}
                className="rounded-md bg-vital-teal px-4 py-2 text-sm font-medium text-chart-cream transition hover:bg-ink-navy"
              >
                Mock exam
              </Link>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
