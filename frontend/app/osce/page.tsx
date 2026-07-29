"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, Subject, Topic } from "@/lib/api";

const OSCE_PREFIX = "OSCE: ";

export default function OscePage() {
  const { user, loading } = useRequireAuth();
  const [subjects, setSubjects] = useState<Subject[] | null>(null);
  const [topics, setTopics] = useState<Topic[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    Promise.all([api.listSubjects(), api.listAllTopics()])
      .then(([s, t]) => {
        setSubjects(s);
        setTopics(t);
      })
      .catch(() => setError("Couldn't load OSCE procedures. Try refreshing."));
  }, [user]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  const osceSubjects = subjects?.filter((s) => s.name.startsWith(OSCE_PREFIX)) ?? [];

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">OSCE</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Clinical skills &amp; procedures
      </h1>
      <p className="mt-3 text-graphite">
        Watch a demonstration, then practice. Pick a procedure below to get started.
      </p>

      {error && <p className="mt-6 text-pulse-coral">{error}</p>}

      {subjects && osceSubjects.length === 0 && (
        <p className="mt-6 text-graphite">
          No OSCE procedures have been added yet — check back soon.
        </p>
      )}

      <div className="mt-10 flex flex-col gap-10">
        {osceSubjects.map((subject) => {
          const subjectTopics = topics?.filter((t) => t.subject_id === subject.id) ?? [];
          if (subjectTopics.length === 0) return null;
          return (
            <section key={subject.id}>
              <h2 className="font-display text-xl font-semibold text-ink-navy">
                {subject.name.slice(OSCE_PREFIX.length)}
              </h2>
              <div className="mt-3 flex flex-col gap-2">
                {subjectTopics.map((topic) => (
                  <Link
                    key={topic.id}
                    href={`/osce/${topic.id}`}
                    className="rounded-md border border-mist px-5 py-3 font-body text-ink-navy transition hover:border-vital-teal hover:bg-card-bg"
                  >
                    {topic.name}
                  </Link>
                ))}
              </div>
            </section>
          );
        })}
      </div>

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
