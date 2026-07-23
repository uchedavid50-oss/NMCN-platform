"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { ApiError } from "@/lib/api";
import { getCGPASummary, addCourse, deleteCourse, CGPASummary } from "@/lib/api-extras";

export default function CGPAPage() {
  const { user, token, loading } = useRequireAuth();
  const [summary, setSummary] = useState<CGPASummary | null>(null);
  const [semester, setSemester] = useState("");
  const [courseName, setCourseName] = useState("");
  const [units, setUnits] = useState(3);
  const [grade, setGrade] = useState("A");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function refresh() {
    if (!token) return;
    getCGPASummary(token).then(setSummary).catch(() => setError("Couldn't load your CGPA data."));
  }

  useEffect(() => {
    if (!user || !token) return;
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, token]);

  async function handleAdd() {
    if (!token || !semester.trim() || !courseName.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await addCourse(semester, courseName, units, grade, token);
      setCourseName("");
      refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't add this course.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!token) return;
    try {
      await deleteCourse(id, token);
      refresh();
    } catch {
      setError("Couldn't delete this course.");
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
    <main className="mx-auto max-w-2xl px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">CGPA Calculator</p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-navy">
        Track your grades across semesters
      </h1>

      {summary && (
        <div className="mt-6 flex gap-4">
          <div className="rounded-md border border-mist p-4">
            <p className="text-xs text-graphite">Cumulative GPA</p>
            <p className="mt-1 font-mono text-3xl text-vital-teal">{summary.cgpa}</p>
          </div>
          <div className="rounded-md border border-mist p-4">
            <p className="text-xs text-graphite">Total units</p>
            <p className="mt-1 font-mono text-3xl text-ink-navy">{summary.total_units}</p>
          </div>
        </div>
      )}

      <div className="mt-8 rounded-md border border-mist bg-card-bg p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">Add a course</p>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <input
            type="text"
            placeholder="Semester (e.g. 300L First Semester)"
            value={semester}
            onChange={(e) => setSemester(e.target.value)}
            className="col-span-2 rounded-md border border-mist px-3 py-2 text-sm"
          />
          <input
            type="text"
            placeholder="Course name"
            value={courseName}
            onChange={(e) => setCourseName(e.target.value)}
            className="col-span-2 rounded-md border border-mist px-3 py-2 text-sm"
          />
          <input
            type="number"
            min={1}
            max={10}
            value={units}
            onChange={(e) => setUnits(Number(e.target.value))}
            placeholder="Units"
            className="rounded-md border border-mist px-3 py-2 text-sm"
          />
          <select
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            className="rounded-md border border-mist px-3 py-2 text-sm"
          >
            {["A", "B", "C", "D", "E", "F"].map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={handleAdd}
          disabled={saving}
          className="mt-3 rounded-md bg-vital-teal px-5 py-2 text-sm font-medium text-chart-cream transition hover:bg-ink-navy disabled:opacity-50"
        >
          {saving ? "Adding…" : "Add course"}
        </button>
        {error && <p className="mt-2 text-sm text-pulse-coral">{error}</p>}
      </div>

      {summary && summary.semesters.length > 0 && (
        <section className="mt-8">
          <h2 className="font-display text-xl font-semibold text-ink-navy">By semester</h2>
          <div className="mt-3 flex flex-col gap-2">
            {summary.semesters.map((s) => (
              <div
                key={s.semester}
                className="flex items-center justify-between rounded-md border border-mist px-4 py-3 text-sm"
              >
                <span className="text-ink-navy">{s.semester}</span>
                <span className="font-mono text-graphite">
                  {s.total_units} units · GPA {s.gpa}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {summary && summary.courses.length > 0 && (
        <section className="mt-8">
          <h2 className="font-display text-xl font-semibold text-ink-navy">All courses</h2>
          <div className="mt-3 flex flex-col gap-2">
            {summary.courses.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between rounded-md border border-mist px-4 py-3 text-sm"
              >
                <div>
                  <span className="text-ink-navy">{c.course_name}</span>
                  <span className="ml-2 text-xs text-graphite">{c.semester}</span>
                </div>
                <div className="flex items-center gap-3 font-mono">
                  <span className="text-graphite">{c.credit_units}u</span>
                  <span className="text-vital-teal">{c.grade}</span>
                  <button
                    onClick={() => handleDelete(c.id)}
                    className="text-pulse-coral hover:underline"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <Link href="/dashboard" className="mt-10 inline-block text-vital-teal hover:underline">
        ← Back to dashboard
      </Link>
    </main>
  );
}
