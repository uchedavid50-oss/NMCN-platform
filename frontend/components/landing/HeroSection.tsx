"use client";

import { useEffect, useRef, type MouseEvent } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion, useMotionValue, useMotionTemplate, useSpring } from "framer-motion";
import gsap from "gsap";
import { Mascot } from "@/components/Mascot";

const MotionLink = motion.create(Link);

const HEADLINE_WORDS = "Know you're ready, before exam day does.".split(" ");

export function HeroSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);

  const mouseX = useMotionValue(50);
  const mouseY = useMotionValue(30);
  const springX = useSpring(mouseX, { stiffness: 60, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 60, damping: 20 });
  const spotlightBackground = useMotionTemplate`radial-gradient(500px circle at ${springX}% ${springY}%, color-mix(in srgb, var(--color-vital-teal) 16%, transparent), transparent 65%)`;

  function handleMouseMove(e: MouseEvent<HTMLElement>) {
    const rect = sectionRef.current?.getBoundingClientRect();
    if (!rect) return;
    mouseX.set(((e.clientX - rect.left) / rect.width) * 100);
    mouseY.set(((e.clientY - rect.top) / rect.height) * 100);
  }

  useEffect(() => {
    if (!headlineRef.current) return;
    const words = headlineRef.current.querySelectorAll("span");
    gsap.fromTo(
      words,
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: 0.6, stagger: 0.06, ease: "power3.out" }
    );
  }, []);

  return (
    <section
      ref={sectionRef}
      onMouseMove={handleMouseMove}
      className="relative mx-auto flex min-h-screen max-w-6xl flex-col items-center gap-10 overflow-hidden px-6 py-16 lg:flex-row"
    >
      <div className="ambient-glow" />
      <motion.div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-[5]" style={{ background: spotlightBackground }} />

      <div className="flex-1">
        <div className="flex items-center gap-3">
          <Mascot className="h-14 w-14 shrink-0" />
          <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
            NMCN Professional Qualifying Examination
          </p>
        </div>
        <h1
          ref={headlineRef}
          className="mt-4 font-display text-4xl font-semibold leading-tight text-ink-navy sm:text-5xl"
        >
          {HEADLINE_WORDS.map((word, i) => (
            <span key={i} className="inline-block opacity-0">
              {word}
              {i < HEADLINE_WORDS.length - 1 ? " " : ""}
            </span>
          ))}
        </h1>
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.5 }}
          className="mt-6 max-w-xl text-lg text-graphite"
        >
          Practice questions, timed mock exams, AI-powered tutoring, and a clear read on
          exactly which topics still need work — built for Nigerian nursing students preparing
          for the NMCN licensing exam.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.75, duration: 0.5 }}
          className="mt-8 flex flex-wrap gap-4"
        >
          <MotionLink
            href="/signup"
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.97 }}
            className="rounded-md bg-vital-teal px-6 py-3 font-body font-medium text-chart-cream shadow-md"
          >
            Create your account
          </MotionLink>
          <MotionLink
            href="/login"
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.97 }}
            className="rounded-md border border-mist px-6 py-3 font-body font-medium text-ink-navy"
          >
            Log in
          </MotionLink>
        </motion.div>
      </div>

      <div className="animate-fade-in-up delay-1 w-full flex-1">
        <div className="relative aspect-[4/5] min-h-[320px] w-full overflow-hidden rounded-2xl border border-mist shadow-xl">
          <Image
            src="/images/hero-nurse.jpg"
            alt="Nursing student studying"
            fill
            className="object-cover"
            priority
          />
        </div>
      </div>
    </section>
  );
}
