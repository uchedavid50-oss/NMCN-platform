"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { getOrgans, getOrganVideo, Organ } from "@/lib/api-extras-9";
import { toYoutubeEmbedUrl } from "@/lib/youtube";

function OrganCard({ organ, token }: { organ: Organ; token: string }) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  useEffect(() => {
    getOrganVideo(organ.id, token)
      .then((v) => setVideoUrl(v.youtube_url))
      .catch(() => setVideoUrl(null));
  }, [organ.id, token]);

  const embedUrl = videoUrl ? toYoutubeEmbedUrl(videoUrl) : null;

  return (
    <div className="rounded-md border border-mist bg-card-bg p-5">
      <p className="font-display text-lg font-semibold text-ink-navy">{organ.name}</p>
      <p className="mt-2 text-sm text-graphite">{organ.description}</p>
      <div className="mt-4">
        {embedUrl ? (
          <div className="aspect-video w-full overflow-hidden rounded-md border border-mist">
            <iframe
              src={embedUrl}
              title={`${organ.name} demonstration`}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              className="h-full w-full"
            />
          </div>
        ) : (
          <p className="rounded-md border border-dashed border-mist p-4 text-center text-xs uppercase tracking-widest text-graphite">
            Video coming soon
          </p>
        )}
      </div>
    </div>
  );
}

export default function OrgansPage() {
  const { user, token, loading } = useRequireAuth();
  const [organs, setOrgans] = useState<Organ[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !token) return;
    getOrgans(token)
      .then(setOrgans)
      .catch(() => setError("Couldn't load organs. Try refreshing."));
  }, [user, token]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Viva</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Organs of the body
      </h1>
      <p className="mt-3 text-graphite">Organ functions and demonstration videos.</p>

      {error && <p className="mt-6 text-pulse-coral">{error}</p>}

      <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {token && organs?.map((organ) => (
          <OrganCard key={organ.id} organ={organ} token={token} />
        ))}
      </div>

      <Link href="/viva" className="mt-10 inline-block text-sm text-vital-teal hover:underline">
        ← Back to Viva
      </Link>
    </main>
  );
}
