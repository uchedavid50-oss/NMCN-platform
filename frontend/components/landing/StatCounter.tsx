"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import gsap from "gsap";

interface Stats {
  students: number;
  questions: number;
  subjects: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function CountUpCard({ label, value, inView }: { label: string; value: number; inView: boolean }) {
  const numberRef = useRef<HTMLParagraphElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!inView || hasAnimated.current || !numberRef.current) return;
    hasAnimated.current = true;
    const counter = { value: 0 };
    gsap.to(counter, {
      value,
      duration: 1.4,
      ease: "power2.out",
      onUpdate: () => {
        if (numberRef.current) numberRef.current.textContent = Math.round(counter.value).toLocaleString();
      },
    });
  }, [inView, value]);

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="rounded-2xl border border-mist bg-card-bg p-6 text-center shadow-md"
    >
      <p ref={numberRef} className="font-display text-4xl font-semibold text-vital-teal">
        0
      </p>
      <p className="mt-2 font-mono text-sm uppercase tracking-widest text-graphite">{label}</p>
    </motion.div>
  );
}

export function StatCounter() {
  const [stats, setStats] = useState<Stats | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const inView = useInView(containerRef, { once: true, margin: "-100px" });

  useEffect(() => {
    fetch(`${API_URL}/public/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  if (!stats) return <div ref={containerRef} />;

  return (
    <div ref={containerRef} className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-3">
      <CountUpCard label="Students preparing" value={stats.students} inView={inView} />
      <CountUpCard label="Practice questions" value={stats.questions} inView={inView} />
      <CountUpCard label="Subjects covered" value={stats.subjects} inView={inView} />
    </div>
  );
}
