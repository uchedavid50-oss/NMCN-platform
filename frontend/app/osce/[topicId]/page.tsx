"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, Topic } from "@/lib/api";
import { getTopicVideo, TopicVideo } from "@/lib/api-extras-8";
import { toYoutubeEmbedUrl } from "@/lib/youtube";

export default function OsceTopicPage() {
  const { topicId } = useParams<{ topicId: string }>();
  const { user, token, loading } = useRequireAuth();
  const [topic, setTopic] = useState<Topic | null>(null);
  const [video, setVideo] = useState<TopicVideo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !token) return;
    api.getTopic(topicId).then(setTopic).catch(() => setError("Couldn't load this procedure."));
    getTopicVideo(topicId, token)
      .then(setVideo)
      .catch((err) => {
        if (!(err instanceof ApiError && err.status === 404)) {
          setError("Couldn't load the demonstration video.");
        }
      });
  }, [user, token, topicId]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  const embedUrl = video ? toYoutubeEmbedUrl(video.youtube_url) : null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">OSCE</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        {topic?.name || "Loading…"}
      </h1>

      {error && <p className="mt-6 text-pulse-coral">{error}</p>}

      <div className="mt-8">
        {video && embedUrl && (
          <div className="aspect-video w-full overflow-hidden rounded-md border border-mist">
            <iframe
              src={embedUrl}
              title={topic?.name || "Procedure demonstration"}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              className="h-full w-full"
            />
          </div>
        )}
        {video && !embedUrl && (
          <a
            href={video.youtube_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-vital-teal hover:underline"
          >
            Watch the demonstration on YouTube →
          </a>
        )}
        {!video && (
          <p className="rounded-md border border-mist bg-card-bg p-5 text-graphite">
            No demonstration video yet for this procedure — check back soon.
          </p>
        )}
      </div>

      <Link
        href={`/practice/${topicId}`}
        className="mt-8 inline-block rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition hover:bg-ink-navy"
      >
        Practice this procedure
      </Link>

      <div className="mt-8">
        <Link href="/osce" className="text-sm text-vital-teal hover:underline">
          ← Back to OSCE
        </Link>
      </div>
    </main>
  );
}
