"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, Subject } from "@/lib/api";

export default function SubjectsPage() {
  const { user, loading } = useRequireAuth();
  const [subjects, setSubjects] = useState<Subject[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api
      .listSubjects()
      .then(setSubjects)
      .catch(() => setError("Couldn't load subjects. Try refreshing."));
  }, [user]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Subjects</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Pick a subject to practice
      </h1>

      {error && <p className="mt-6 text-pulse-coral">{error}</p>}

      {subjects && subjects.length === 0 && (
        <p className="mt-6 text-graphite">
          No subjects have been added yet — check back soon.
        </p>
      )}

      <div className="mt-8 flex flex-col gap-3">
        {subjects?.map((subject) => (
          <Link
            key={subject.id}
            href={`/subjects/${subject.id}`}
            className="rounded-md border border-mist px-5 py-4 font-body text-lg text-ink-navy transition hover:border-vital-teal hover:bg-white"
          >
            {subject.name}
          </Link>
        ))}
      </div>
    </main>
  );
}
