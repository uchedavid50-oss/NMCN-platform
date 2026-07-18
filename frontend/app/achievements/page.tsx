"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, Badge, CertificateEligibility } from "@/lib/api";

export default function AchievementsPage() {
  const { user, token, loading } = useRequireAuth();
  const [badges, setBadges] = useState<Badge[] | null>(null);
  const [eligibility, setEligibility] = useState<CertificateEligibility | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!user || !token) return;
    Promise.all([api.getBadges(token), api.getCertificateEligibility(token)])
      .then(([b, e]) => {
        setBadges(b);
        setEligibility(e);
      })
      .catch(() => setError("Couldn't load your achievements."));
  }, [user, token]);

  async function handleDownload() {
    if (!token) return;
    setDownloading(true);
    setError(null);
    try {
      await api.downloadCertificate(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't download the certificate.");
    } finally {
      setDownloading(false);
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
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Achievements</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Badges &amp; your completion certificate
      </h1>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      <section className="mt-8 rounded-md border border-mist bg-card-bg p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">
          Completion certificate
        </p>
        <p className="mt-1 text-sm text-graphite">
          Reflects genuine, sustained platform practice — it is <strong>not</strong> an official
          NMCN credential and does not guarantee real exam results.
        </p>

        {eligibility && (
          <div className="mt-4">
            {eligibility.eligible ? (
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="rounded-md bg-vital-teal px-6 py-2.5 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
              >
                {downloading ? "Preparing…" : "Download certificate (PDF)"}
              </button>
            ) : (
              <p className="text-sm text-graphite">
                Not yet eligible: <span className="text-pulse-coral">{eligibility.reason}</span>
              </p>
            )}
          </div>
        )}
      </section>

      <section className="mt-8">
        <h2 className="font-display text-xl font-semibold text-ink-navy">Badges</h2>
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {badges?.map((badge) => (
            <div
              key={badge.id}
              className={`rounded-md border p-4 text-center ${
                badge.earned ? "border-vital-teal bg-vital-teal/10" : "border-mist opacity-50"
              }`}
            >
              <p className="text-2xl">{badge.earned ? "🏅" : "🔒"}</p>
              <p className="mt-2 font-medium text-ink-navy">{badge.name}</p>
              <p className="mt-1 text-xs text-graphite">{badge.description}</p>
            </div>
          ))}
        </div>
      </section>

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
