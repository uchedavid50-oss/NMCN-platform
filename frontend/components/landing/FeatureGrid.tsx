"use client";

import Link from "next/link";
import { motion, type Variants } from "framer-motion";

const FEATURES = [
  {
    icon: "🎓",
    title: "Full CBT Exam Simulation",
    description: "A real, timed, mixed-subject exam — the closest thing to the real NMCN exam day.",
  },
  {
    icon: "🩺",
    title: "Clinical Case Simulator",
    description: "Work through realistic patient scenarios, decision by decision, with instant feedback.",
  },
  {
    icon: "🤖",
    title: "AI Tutor",
    description: "Get answers explained in plain language, and a personalized study plan for weak topics.",
  },
  {
    icon: "📝",
    title: "Your Notes → Questions",
    description: "Upload your own study notes and get private practice questions generated from them.",
  },
  {
    icon: "🔥",
    title: "Streaks & Speed Rounds",
    description: "Build a daily practice habit with quick arcade-style rounds and a running streak.",
  },
  {
    icon: "📚",
    title: "Textbook Library & Dictionary",
    description: "Browse reference textbooks and look up nursing terms instantly.",
  },
];

const containerVariants: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

export function FeatureGrid() {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-80px" }}
      className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      {FEATURES.map((f, i) => (
        <motion.div key={f.title} variants={itemVariants}>
          <Link
            href="/signup"
            style={{ transitionTimingFunction: "cubic-bezier(0.68, -0.55, 0.265, 1.55)" }}
            className="group relative block h-full rounded-2xl border-[3px] border-mist bg-card-bg p-6 shadow-md transition-all duration-300 hover:-translate-y-2 hover:rotate-1 hover:border-vital-teal hover:shadow-2xl active:scale-90"
          >
            <span
              className="absolute -right-1 -top-1 text-xl opacity-0 group-hover:animate-sparkle"
              aria-hidden
            >
              ✨
            </span>
            <span
              className="absolute -left-2 top-8 text-lg opacity-0 group-hover:animate-sparkle"
              style={{ animationDelay: "0.15s" }}
              aria-hidden
            >
              ✨
            </span>
            <p
              className="animate-cartoon-bob group-hover:animate-jiggle inline-block text-4xl"
              style={{ animationDelay: `${i * 0.15}s` }}
            >
              {f.icon}
            </p>
            <p className="mt-3 font-display text-lg font-semibold text-ink-navy transition-colors group-hover:text-vital-teal">
              {f.title}
            </p>
            <p className="mt-2 text-sm text-graphite">{f.description}</p>
            <p className="mt-3 text-xs font-bold text-vital-teal opacity-0 transition-opacity duration-200 group-hover:opacity-100">
              Try it free →
            </p>
          </Link>
        </motion.div>
      ))}
    </motion.div>
  );
}
