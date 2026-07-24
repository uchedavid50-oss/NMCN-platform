import Link from "next/link";
import { PulseTrace } from "@/components/PulseTrace";
import { ThemeToggle } from "@/components/ThemeToggle";
export default function Home() {
  return (
    <main className="relative mx-auto flex min-h-screen max-w-3xl flex-col justify-center overflow-hidden px-6 py-16">
      <div className="ambient-glow" />
      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>
      <p className="animate-fade-in-up font-mono text-sm uppercase tracking-widest text-vital-teal">
        NMCN Professional Qualifying Examination
      </p>
      <h1 className="animate-fade-in-up delay-1 mt-4 font-display text-5xl font-semibold leading-tight text-ink-navy">
        Know you&apos;re ready, before exam day does.
      </h1>
      <p className="animate-fade-in-up delay-2 mt-6 max-w-xl text-lg text-graphite">
        Practice questions, timed mock exams, and a clear read on exactly which
        topics still need work — built for the NMCN licensing exam.
      </p>
      <div className="animate-fade-in-up delay-3">
        <PulseTrace className="my-10 h-16 w-full max-w-md" />
      </div>
      <div className="animate-fade-in-up delay-4 flex gap-4">
        <Link
          href="/signup"
          className="rounded-md bg-vital-teal px-6 py-3 font-body font-medium text-chart-cream transition-all duration-200 hover:-translate-y-0.5 hover:bg-ink-navy hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-vital-teal"
        >
          Create your account
        </Link>
        <Link
          href="/login"
          className="rounded-md border border-mist px-6 py-3 font-body font-medium text-ink-navy transition-all duration-200 hover:-translate-y-0.5 hover:border-vital-teal hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-vital-teal"
        >
          Log in
        </Link>
      </div>
    </main>
  );
}
