"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, UserSession } from "@/lib/api";

function formatDate(iso: string) {
  return new Date(iso.endsWith("Z") ? iso : `${iso}Z`).toLocaleString();
}

export default function DevicesSettingsPage() {
  const { user, token, loading } = useRequireAuth();
  const [sessions, setSessions] = useState<UserSession[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .listSessions(token)
      .then(setSessions)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Couldn't load your devices."));
  }, [token]);

  async function handleLogoutDevice(sessionId: string) {
    if (!token) return;
    setRemovingId(sessionId);
    setError(null);
    try {
      await api.deleteSession(sessionId, token);
      setSessions((prev) => (prev ? prev.filter((s) => s.id !== sessionId) : prev));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't log out that device.");
    } finally {
      setRemovingId(null);
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
    <main className="mx-auto max-w-xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Security</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">Devices</h1>
      <p className="mt-3 text-graphite">
        Your account is limited to 2 active devices at a time. Log out a device here to free up a
        slot for a new one.
      </p>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      <div className="mt-6 flex flex-col gap-3">
        {sessions === null && !error && <p className="text-graphite">Loading devices…</p>}

        {sessions?.map((session) => (
          <div
            key={session.id}
            className={`rounded-md border p-5 ${
              session.is_current ? "border-vital-teal bg-vital-teal/10" : "border-mist bg-card-bg"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-medium text-ink-navy">
                  {session.device_label}
                  {session.is_current && (
                    <span className="ml-2 font-mono text-xs uppercase tracking-widest text-vital-teal">
                      This device
                    </span>
                  )}
                </p>
                <p className="mt-1 text-sm text-graphite">
                  Last active {formatDate(session.last_active_at)}
                </p>
              </div>
              <button
                onClick={() => handleLogoutDevice(session.id)}
                disabled={removingId === session.id}
                className="shrink-0 rounded-md border border-pulse-coral px-3 py-1.5 text-sm font-medium text-pulse-coral transition hover:bg-pulse-coral/10 disabled:opacity-50"
              >
                {removingId === session.id ? "Logging out…" : "Log out this device"}
              </button>
            </div>
          </div>
        ))}

        {sessions && sessions.length === 0 && (
          <p className="text-graphite">No active devices found.</p>
        )}
      </div>

      <div className="mt-10 flex flex-col gap-2">
        <Link href="/settings/security" className="text-vital-teal hover:underline">
          Two-factor authentication settings →
        </Link>
        <Link href="/dashboard" className="text-vital-teal hover:underline">
          ← Back to dashboard
        </Link>
      </div>
    </main>
  );
}
