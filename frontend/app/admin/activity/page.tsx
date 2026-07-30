"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import {
  getAdminSummary,
  getRecentUsers,
  getRecentPayments,
  AdminSummary,
  AdminUser,
  AdminPayment,
} from "@/lib/api-extras-11";

function formatNaira(kobo: number) {
  return `₦${(kobo / 100).toLocaleString()}`;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString();
}

export default function AdminActivityPage() {
  const { user, token, loading } = useRequireAuth();
  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [payments, setPayments] = useState<AdminPayment[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    getAdminSummary(token).then(setSummary).catch(() => {});
    getRecentUsers(token, 50).then(setUsers).catch(() => setError("Couldn't load recent signups."));
    getRecentPayments(token, 50).then(setPayments).catch(() => setError("Couldn't load recent payments."));
  }, [token]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  if (user.role !== "admin") {
    return (
      <main className="mx-auto max-w-xl px-6 py-16 text-center">
        <p className="text-pulse-coral">This page is admin-only.</p>
        <Link href="/dashboard" className="mt-4 inline-block text-vital-teal hover:underline">
          ← Back to dashboard
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Admin</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">Signups &amp; payments</h1>

      {error && <p className="mt-4 text-sm text-pulse-coral">{error}</p>}

      {summary && (
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-5">
          <div className="rounded-md border border-mist bg-card-bg p-4 text-center">
            <p className="font-display text-2xl font-semibold text-ink-navy">{summary.total_students}</p>
            <p className="mt-1 font-mono text-xs uppercase tracking-widest text-graphite">Students</p>
          </div>
          <div className="rounded-md border border-mist bg-card-bg p-4 text-center">
            <p className="font-display text-2xl font-semibold text-vital-teal">{summary.signups_today}</p>
            <p className="mt-1 font-mono text-xs uppercase tracking-widest text-graphite">Signups today</p>
          </div>
          <div className="rounded-md border border-mist bg-card-bg p-4 text-center">
            <p className="font-display text-2xl font-semibold text-ink-navy">{summary.active_subscriptions}</p>
            <p className="mt-1 font-mono text-xs uppercase tracking-widest text-graphite">Active subs</p>
          </div>
          <div className="rounded-md border border-mist bg-card-bg p-4 text-center">
            <p className="font-display text-2xl font-semibold text-vital-teal">
              {formatNaira(summary.total_revenue_kobo)}
            </p>
            <p className="mt-1 font-mono text-xs uppercase tracking-widest text-graphite">Total revenue</p>
          </div>
          <div className="rounded-md border border-mist bg-card-bg p-4 text-center">
            <p className="font-display text-2xl font-semibold text-ink-navy">{summary.total_admins}</p>
            <p className="mt-1 font-mono text-xs uppercase tracking-widest text-graphite">Admins</p>
          </div>
        </div>
      )}

      <section className="mt-10">
        <h2 className="font-display text-xl font-semibold text-ink-navy">Recent signups</h2>
        <div className="mt-3 flex flex-col gap-2">
          {users.length === 0 && <p className="text-sm text-graphite">No signups yet.</p>}
          {users.map((u) => (
            <div
              key={u.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-mist px-4 py-3 text-sm"
            >
              <span className="text-ink-navy">{u.email}</span>
              <span className="flex items-center gap-3 text-graphite">
                <span className="font-mono text-xs uppercase tracking-widest">{u.role}</span>
                <span>{formatDate(u.created_at)}</span>
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-10">
        <h2 className="font-display text-xl font-semibold text-ink-navy">Recent payments</h2>
        <div className="mt-3 flex flex-col gap-2">
          {payments.length === 0 && <p className="text-sm text-graphite">No payment attempts yet.</p>}
          {payments.map((p) => (
            <div
              key={p.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-mist px-4 py-3 text-sm"
            >
              <div>
                <p className="text-ink-navy">{p.user_email}</p>
                <p className="text-xs text-graphite">
                  {p.plan} · {formatNaira(p.amount_kobo)}
                </p>
              </div>
              <span className="flex items-center gap-3 text-graphite">
                <span
                  className={`font-mono text-xs uppercase tracking-widest ${
                    p.status === "active"
                      ? "text-vital-teal"
                      : p.status === "failed"
                      ? "text-pulse-coral"
                      : "text-graphite"
                  }`}
                >
                  {p.status}
                </span>
                <span>{formatDate(p.created_at)}</span>
              </span>
            </div>
          ))}
        </div>
      </section>

      <Link href="/dashboard" className="mt-10 inline-block text-sm text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
