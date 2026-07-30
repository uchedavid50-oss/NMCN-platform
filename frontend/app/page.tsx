import Link from "next/link";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Mascot } from "@/components/Mascot";
import { HeroSection } from "@/components/landing/HeroSection";
import { StatCounter } from "@/components/landing/StatCounter";
import { FeatureGrid } from "@/components/landing/FeatureGrid";
import { FadeInSection } from "@/components/landing/FadeInSection";
import { InfiniteMovingCards, MovingCardItem } from "@/components/landing/InfiniteMovingCards";

// Not testimonials attributed to invented people -- honest feature
// highlights cycled through the same moving-cards mechanism until real
// student reviews exist (see the intro copy in the Reviews section below).
const HIGHLIGHT_CARDS: MovingCardItem[] = [
  { text: "Timed mock exams that mirror the real NMCN CBT format." },
  { text: "An AI tutor on call whenever you're stuck on a concept." },
  { text: "Practice questions across every subject in the curriculum." },
  { text: "See exactly which topics still need work, backed by your own attempt history." },
  { text: "Upload your own notes and get private practice questions generated from them." },
  { text: "Free to start — no credit card required." },
];

export default function Home() {
  return (
    <main className="relative overflow-hidden">
      <div className="absolute right-6 top-6 z-10">
        <ThemeToggle />
      </div>

      <HeroSection />

      {/* Stats */}
      <section className="mx-auto max-w-6xl px-6">
        <StatCounter />
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-center font-display text-3xl font-semibold text-ink-navy">
          Everything you need to walk into exam day ready
        </h2>
        <FeatureGrid />
      </section>

      {/* Pricing */}
      <FadeInSection className="mx-auto max-w-4xl px-6 py-16">
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
      </FadeInSection>

      {/* Reviews - honest placeholder, no fabricated testimonials */}
      <FadeInSection className="mx-auto max-w-4xl px-6 py-16 text-center">
        <h2 className="font-display text-3xl font-semibold text-ink-navy">From our students</h2>
        <div className="mt-4 flex flex-col items-center gap-3">
          <Mascot className="h-16 w-16" wave={false} />
          <p className="max-w-xl text-graphite">
            We&apos;re just getting started — real reviews from real students will show up here
            as more people join. Be one of the first. In the meantime, here&apos;s what&apos;s
            already built for you:
          </p>
        </div>
        <div className="mt-8">
          <InfiniteMovingCards items={HIGHLIGHT_CARDS} />
        </div>
      </FadeInSection>

      {/* Final CTA */}
      <FadeInSection className="mx-auto max-w-3xl px-6 py-16 text-center">
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
      </FadeInSection>
    </main>
  );
}
