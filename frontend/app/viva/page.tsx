"use client";

import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";

export default function VivaPage() {
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
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Viva</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Viva voce preparation
      </h1>
      <p className="mt-3 text-graphite">
        Get ready for the practical and oral components of your exam.
      </p>

      <div className="mt-10 flex flex-col gap-4">
        <Link
          href="/viva/equipment"
          className="rounded-md border border-mist bg-card-bg px-6 py-5 transition hover:border-vital-teal"
        >
          <p className="font-display text-lg font-semibold text-ink-navy">Equipment</p>
          <p className="mt-1 text-sm text-graphite">
            Video demonstration and reference PDF covering nursing equipment.
          </p>
        </Link>
        <Link
          href="/viva/organs"
          className="rounded-md border border-mist bg-card-bg px-6 py-5 transition hover:border-vital-teal"
        >
          <p className="font-display text-lg font-semibold text-ink-navy">Organs</p>
          <p className="mt-1 text-sm text-graphite">
            Organs of the body, their functions, and demonstration videos.
          </p>
        </Link>
      </div>

      <Link href="/dashboard" className="mt-10 inline-block text-sm text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
