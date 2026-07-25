import Link from "next/link";
import Image from "next/image";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Mascot } from "@/components/Mascot";

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

export default function Home() {
  return (
    <main className="relative overflow-hidden">
      <div className="absolute right-6 top-6 z-10">
        <ThemeToggle />
      </div>

      {/* Hero */}
      <section className="relative mx-auto flex min-h-screen max-w-6xl flex-col items-center gap-10 overflow-hidden px-6 py-16 lg:flex-row">
        <div className="ambient-glow" />
        <div className="animate-fade-in-up flex-1">
          <div className="flex items-center gap-3">
            <Mascot className="h-14 w-14 shrink-0" />
            <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
              NMCN Professional Qualifying Examination
            </p>
          </div>
          <h1 className="mt-4 font-display text-4xl font-semibold leading-tight text-ink-navy sm:text-5xl">
            Know you&apos;re ready, before exam day does.
          </h1>
          <p className="mt-6 max-w-xl text-lg text-graphite">
            Practice questions, timed mock exams, AI-powered tutoring, and a clear read on
            exactly which topics still need work — built for Nigerian nursing students preparing
            for the NMCN licensing exam.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/signup"
              className="rounded-md bg-vital-teal px-6 py-3 font-body font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg"
            >
              Create your account
            </Link>
            <Link
              href="/login"
              className="rounded-md border border-mist px-6 py-3 font-body font-medium text-ink-navy transition-all duration-200 hover:-translate-y-0.5 hover:border-vital-teal hover:shadow-md"
            >
              Log in
            </Link>
          </div>
        </div>
        <div className="animate-fade-in-up delay-1 w-full flex-1">
          <div className="relative aspect-[4/5] min-h-[320px] w-full overflow-hidden rounded-2xl border border-mist shadow-xl">
            {/*
              Download a free-to-use photo from Unsplash (search "nurse" or
              "nursing student") and save it as:
              frontend/public/images/hero-nurse.jpg
              Recommended size: at least 800x1000px, portrait orientation.
            */}
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

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-center font-display text-3xl font-semibold text-ink-navy">
          Everything you need to walk into exam day ready
        </h2>
        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <Link
              key={f.title}
              href="/signup"
              style={{ transitionTimingFunction: "cubic-bezier(0.68, -0.55, 0.265, 1.55)" }}
              className="group relative block rounded-2xl border-[3px] border-mist bg-card-bg p-6 shadow-md transition-all duration-300 hover:-translate-y-2 hover:rotate-1 hover:border-vital-teal hover:shadow-2xl active:scale-90"
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
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="mx-auto max-w-4xl px-6 py-16">
        <h2 className="text-center font-display text-3xl font-semibold text-ink-navy">
          Start free. Upgrade when you&apos;re ready.
        </h2>
        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div className="auth-card p-8">
            <p className="font-mono text-xs uppercase tracking-widest text-graphite">Free</p>
            <p className="mt-2 font-display text-3xl font-semibold text-ink-navy">₦0</p>
            <ul className="mt-6 flex flex-col gap-3 text-sm text-graphite">
              <li>✓ Unlimited practice questions</li>
              <li>✓ Flashcards &amp; speed rounds</li>
              <li>✓ AI tutor &amp; study plans</li>
              <li>✓ 3 mock exams</li>
              <li>✓ 1 full CBT exam simulation</li>
            </ul>
            <Link
              href="/signup"
              className="mt-8 inline-block w-full rounded-md border border-mist px-6 py-3 text-center font-medium text-ink-navy transition-all hover:border-vital-teal hover:shadow-md"
            >
              Get started free
            </Link>
          </div>
          <div className="auth-card relative overflow-hidden border-2 border-vital-teal p-8">
            <p className="absolute right-4 top-4 rounded-full bg-vital-teal px-3 py-1 text-xs font-medium text-chart-cream">
              One-time
            </p>
            <p className="font-mono text-xs uppercase tracking-widest text-vital-teal">Premium</p>
            <p className="mt-2 font-display text-3xl font-semibold text-ink-navy">
              ₦5,000 <span className="text-base font-normal text-graphite">once, forever</span>
            </p>
            <ul className="mt-6 flex flex-col gap-3 text-sm text-graphite">
              <li>✓ Everything in Free</li>
              <li>✓ Unlimited mock exams</li>
              <li>✓ Unlimited full CBT exam simulations</li>
              <li>✓ Lifetime access — pay once, never again</li>
            </ul>
            <Link
              href="/signup"
              className="mt-8 inline-block w-full rounded-md bg-vital-teal px-6 py-3 text-center font-medium text-chart-cream transition-all hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg"
            >
              Get premium
            </Link>
          </div>
        </div>
      </section>

      {/* Reviews - honest placeholder, no fabricated testimonials */}
      <section className="mx-auto max-w-3xl px-6 py-16 text-center">
        <h2 className="font-display text-3xl font-semibold text-ink-navy">From our students</h2>
        <div className="auth-card mt-8 p-10">
          <Mascot className="mx-auto h-16 w-16" wave={false} />
          <p className="mt-4 text-graphite">
            We&apos;re just getting started — real reviews from real students will show up here
            as more people join. Be one of the first.
          </p>
        </div>
      </section>

      {/* Final CTA */}
      <section className="mx-auto max-w-3xl px-6 py-16 text-center">
        <h2 className="font-display text-3xl font-semibold text-ink-navy">
          Ready to know where you stand?
        </h2>
        <div className="mt-6 flex justify-center gap-4">
          <Link
            href="/signup"
            className="rounded-md bg-vital-teal px-6 py-3 font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg"
          >
            Create your account
          </Link>
          <Link
            href="/login"
            className="rounded-md border border-mist px-6 py-3 font-medium text-ink-navy transition-all duration-200 hover:-translate-y-0.5 hover:border-vital-teal hover:shadow-md"
          >
            Log in
          </Link>
        </div>
      </section>
    </main>
  );
}
