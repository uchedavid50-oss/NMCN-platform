"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useRequireAuth } from "@/lib/use-require-auth";
import { useTheme } from "@/lib/theme-context";
import { api, Subject } from "@/lib/api";

interface SubjectProgress {
  subject: Subject;
  totalTopics: number;
  attemptedTopics: number;
}

const NAV_SECTIONS: { title: string; items: { href: string; label: string; icon: string }[] }[] = [
  {
    title: "Practice",
    items: [
      { href: "/subjects", label: "Subjects", icon: "📚" },
      { href: "/games/speed-round", label: "Speed round", icon: "⚡" },
      { href: "/cbt-exam", label: "CBT Center", icon: "🎓" },
      { href: "/clinical-cases", label: "Clinical Cases", icon: "🩺" },
    ],
  },
  {
    title: "Study tools",
    items: [
      { href: "/notes", label: "My notes", icon: "📝" },
      { href: "/cgpa", label: "CGPA Calculator", icon: "📊" },
      { href: "/mnemonics", label: "Mnemonics", icon: "💡" },
      { href: "/focus", label: "Focus Session", icon: "🧘" },
      { href: "/dictionary", label: "Nursing Dictionary", icon: "📖" },
      { href: "/textbooks", label: "Textbook Library", icon: "🗂️" },
    ],
  },
  {
    title: "Progress & community",
    items: [
      { href: "/analytics", label: "My progress", icon: "📈" },
      { href: "/leaderboard", label: "Leaderboard", icon: "🏆" },
      { href: "/achievements", label: "Achievements", icon: "🏅" },
    ],
  },
];

function ProfileMenu({ isAdmin }: { isAdmin: boolean }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [coords, setCoords] = useState({ top: 0, right: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleToggle() {
    if (!open && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setCoords({ top: rect.bottom + 8, right: window.innerWidth - rect.right });
    }
    setOpen((o) => !o);
  }

  const initial = (user?.display_name || user?.email || "?").trim()[0]?.toUpperCase() || "?";

  return (
    <>
      <button
        ref={buttonRef}
        onClick={handleToggle}
        className="flex h-10 w-10 items-center justify-center rounded-full border border-vital-teal font-mono text-sm font-semibold text-vital-teal transition-transform hover:scale-105"
      >
        {initial}
      </button>
      {mounted &&
        open &&
        createPortal(
          <div
            ref={menuRef}
            style={{ position: "fixed", top: coords.top, right: coords.right }}
            className="auth-card z-50 w-64 p-2"
          >
            <div className="border-b border-mist px-3 py-3">
              <p className="font-medium text-ink-navy">{user?.display_name || "Student"}</p>
              <p className="text-xs text-graphite">{user?.email}</p>
            </div>
            <div className="flex flex-col py-1">
              <button
                onClick={toggleTheme}
                className="rounded-md px-3 py-2 text-left text-sm text-ink-navy transition-colors hover:bg-mist/40"
              >
                {theme === "light" ? "🌙 Switch to dark mode" : "☀️ Switch to light mode"}
              </button>
              <Link
                href="/settings/security"
                onClick={() => setOpen(false)}
                className="rounded-md px-3 py-2 text-left text-sm text-ink-navy transition-colors hover:bg-mist/40"
              >
                🔒 Security settings
              </Link>
              <Link
                href="/subscribe"
                onClick={() => setOpen(false)}
                className="rounded-md px-3 py-2 text-left text-sm text-ink-navy transition-colors hover:bg-mist/40"
              >
                💳 Subscription
              </Link>
              {isAdmin && (
                <Link
                  href="/admin/content"
                  onClick={() => setOpen(false)}
                  className="rounded-md px-3 py-2 text-left text-sm text-pulse-coral transition-colors hover:bg-pulse-coral/10"
                >
                  ⚙️ Admin: Content
                </Link>
              )}
              <button
                onClick={logout}
                className="rounded-md px-3 py-2 text-left text-sm text-graphite transition-colors hover:bg-mist/40"
              >
                Log out
              </button>
            </div>
          </div>,
          document.body
        )}
    </>
  );
}

function SubjectCard({
  subject,
  totalTopics,
  attemptedTopics,
}: {
  subject: Subject;
  totalTopics: number;
  attemptedTopics: number;
}) {
  const percent = totalTopics > 0 ? Math.round((attemptedTopics / totalTopics) * 100) : 0;
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const t = setTimeout(() => setWidth(percent), 150);
    return () => clearTimeout(t);
  }, [percent]);

  return (
    <Link
      href={`/subjects/${subject.id}`}
      className="group auth-card relative block overflow-hidden border-2 border-transparent p-5 transition-all hover:-translate-y-0.5 hover:border-vital-teal"
    >
      <div className="relative pr-20">
        <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">NMCN Subject</p>
        <p className="mt-1 font-display text-lg font-semibold text-ink-navy">{subject.name}</p>
        <p className="mt-2 text-sm text-graphite">
          {attemptedTopics} of {totalTopics} topics started · {percent}%
        </p>
        <span className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 rounded-full bg-vital-teal px-4 py-1.5 text-xs font-medium text-chart-cream opacity-0 shadow-md transition-all duration-200 group-hover:translate-x-0 group-hover:opacity-100">
          {attemptedTopics > 0 ? "▶ Resume" : "▶ Start"}
        </span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-mist">
        <div
          className="h-full rounded-full bg-vital-teal transition-all duration-700 ease-out"
          style={{ width: `${width}%` }}
        />
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const { user, token, loading } = useRequireAuth();
  const pathname = usePathname();
  const [streak, setStreak] = useState<number | null>(null);
  const [playedToday, setPlayedToday] = useState<boolean | null>(null);
  const [subjectProgress, setSubjectProgress] = useState<SubjectProgress[] | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .getStreak(token)
      .then((s) => {
        setStreak(s.current_streak);
        setPlayedToday(s.played_today);
      })
      .catch(() => {
        setStreak(0);
        setPlayedToday(false);
      });
  }, [token]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function loadProgress() {
      try {
        const [subjects, performance] = await Promise.all([
          api.listSubjects(),
          api.getByTopic(token!),
        ]);
        const results: SubjectProgress[] = [];
        for (const subject of subjects) {
          const topics = await api.listTopics(subject.id);
          const attempted = performance.filter(
            (p) => p.subject_name === subject.name && p.total_answered > 0
          ).length;
          results.push({ subject, totalTopics: topics.length, attemptedTopics: attempted });
        }
        if (!cancelled) setSubjectProgress(results);
      } catch {
        if (!cancelled) setSubjectProgress([]);
      }
    }

    loadProgress();
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (loading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-sm text-graphite">Loading…</p>
      </main>
    );
  }

  return (
    <div className="relative flex min-h-screen overflow-hidden">
      <div className="ambient-glow" />

      {/* Sidebar */}
      <aside className="hidden w-56 shrink-0 border-r border-mist bg-card-bg px-4 py-8 md:block">
        <p className="px-2 font-display text-lg font-semibold text-ink-navy">NMCN CBT Prep</p>
        <nav className="mt-8 flex flex-col gap-6">
          <Link
            href="/dashboard"
            className={`flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition-colors ${
              pathname === "/dashboard"
                ? "bg-vital-teal/15 text-vital-teal"
                : "text-ink-navy hover:bg-vital-teal/10 hover:text-vital-teal"
            }`}
          >
            <span>🏠</span> Home
          </Link>
          {NAV_SECTIONS.map((section) => (
            <div key={section.title}>
              <p className="px-2 font-mono text-xs uppercase tracking-widest text-graphite">
                {section.title}
              </p>
              <div className="mt-2 flex flex-col gap-1">
                {section.items.map((item) => {
                  const active = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-2 rounded-full px-3 py-2 text-sm transition-colors ${
                        active
                          ? "bg-vital-teal/15 font-medium text-vital-teal"
                          : "text-ink-navy hover:bg-vital-teal/10 hover:text-vital-teal"
                      }`}
                    >
                      <span>{item.icon}</span> {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 px-6 py-10 sm:px-10">
        <div className="animate-fade-in-up flex items-center justify-between">
          <div>
            <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">Dashboard</p>
            <h1 className="mt-1 font-display text-2xl font-semibold text-ink-navy sm:text-3xl">
              Hi, {user.display_name || user.email} 👋
            </h1>
          </div>
          <ProfileMenu isAdmin={user.role === "admin"} />
        </div>

        {playedToday === false && (
          <div className="animate-fade-in-up delay-1 mt-6 flex items-center justify-between rounded-md border border-pulse-coral bg-pulse-coral/10 px-5 py-4">
            <p className="text-sm text-ink-navy">
              {streak && streak > 0 ? (
                <>
                  🔥 You have a <strong>{streak}-day streak</strong> — practice today to keep it
                  alive!
                </>
              ) : (
                <>Haven&apos;t practiced today yet — even one quick round starts a streak.</>
              )}
            </p>
            <Link
              href="/games/speed-round"
              className="ml-4 whitespace-nowrap rounded-md bg-pulse-coral px-4 py-2 text-sm font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg"
            >
              Quick round →
            </Link>
          </div>
        )}

        <div className="animate-fade-in-up delay-2 mt-8 grid grid-cols-3 gap-4 font-mono text-sm">
          <div className="rounded-md border border-mist bg-card-bg p-4 transition-shadow hover:shadow-md">
            <p className="text-graphite">Role</p>
            <p className="mt-1 text-lg text-ink-navy">{user.role}</p>
          </div>
          <Link
            href="/subscribe"
            className="rounded-md border border-mist bg-card-bg p-4 transition-all hover:-translate-y-0.5 hover:border-vital-teal hover:shadow-md"
          >
            <p className="text-graphite">Subscription</p>
            <p className="mt-1 text-lg text-ink-navy">
              {user.subscription_status === "active" ? "Premium ✓" : "Free — upgrade →"}
            </p>
          </Link>
          <div className="rounded-md border border-mist bg-card-bg p-4 transition-shadow hover:shadow-md">
            <p className="text-graphite">Streak</p>
            <p className="mt-1 text-lg text-pulse-coral">
              {streak === null ? "…" : `🔥 ${streak} day${streak === 1 ? "" : "s"}`}
            </p>
          </div>
        </div>

        <section className="animate-fade-in-up delay-3 mt-10">
          <h2 className="font-display text-xl font-semibold text-ink-navy">Continue practicing</h2>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {subjectProgress?.map(({ subject, totalTopics, attemptedTopics }) => (
              <SubjectCard
                key={subject.id}
                subject={subject}
                totalTopics={totalTopics}
                attemptedTopics={attemptedTopics}
              />
            ))}
            {subjectProgress && subjectProgress.length === 0 && (
              <p className="text-graphite">No subjects available yet.</p>
            )}
            {!subjectProgress && <p className="text-graphite">Loading your subjects…</p>}
          </div>
        </section>
      </main>
    </div>
  );
}
