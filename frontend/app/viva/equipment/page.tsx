"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ApiError } from "@/lib/api";
import { getEquipment, downloadEquipmentPdf, Equipment } from "@/lib/api-extras-9";
import { toYoutubeEmbedUrl } from "@/lib/youtube";

export default function EquipmentPage() {
  const { user, token, loading } = useRequireAuth();
  const [equipment, setEquipment] = useState<Equipment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!user || !token) return;
    getEquipment(token)
      .then(setEquipment)
      .catch(() => setError("Couldn't load equipment content."));
  }, [user, token]);

  async function handleDownload() {
    if (!token) return;
    setDownloading(true);
    setError(null);
    try {
      await downloadEquipmentPdf(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't download the PDF.");
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

  const embedUrl = equipment?.youtube_url ? toYoutubeEmbedUrl(equipment.youtube_url) : null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Viva</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        {equipment?.title || "Nursing Equipment"}
      </h1>
      {equipment?.description && (
        <p className="mt-3 text-graphite">{equipment.description}</p>
      )}

      {error && <p className="mt-6 text-pulse-coral">{error}</p>}

      <div className="mt-8">
        {equipment?.youtube_url && embedUrl && (
          <div className="aspect-video w-full overflow-hidden rounded-md border border-mist">
            <iframe
              src={embedUrl}
              title="Equipment demonstration"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              className="h-full w-full"
            />
          </div>
        )}
        {equipment?.youtube_url && !embedUrl && (
          <a
            href={equipment.youtube_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-vital-teal hover:underline"
          >
            Watch the demonstration on YouTube →
          </a>
        )}
        {!equipment?.youtube_url && (
          <p className="rounded-md border border-mist bg-card-bg p-5 text-graphite">
            No equipment video yet — check back soon.
          </p>
        )}
      </div>

      <div className="mt-6">
        {equipment?.pdf_filename ? (
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
          >
            {downloading ? "Downloading…" : `Download PDF (${equipment.pdf_filename})`}
          </button>
        ) : (
          <p className="rounded-md border border-mist bg-card-bg p-5 text-graphite">
            No equipment PDF yet — check back soon.
          </p>
        )}
      </div>

      <Link href="/viva" className="mt-10 inline-block text-sm text-vital-teal hover:underline">
        ← Back to Viva
      </Link>
    </main>
  );
}
