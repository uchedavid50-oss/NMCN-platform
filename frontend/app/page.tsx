import Link from "next/link";
import { PulseTrace } from "@/components/PulseTrace";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-widest text-vital-teal">
        NMCN Professional Qualifying Examination
      </p>
      <h1 className="mt-4 font-display text-5xl font-semibold leading-tight text-ink-navy">
        Know you&apos;re ready, before exam day does.
      </h1>
      <p className="mt-6 max-w-xl text-lg text-graphite">
        Practice questions, timed mock exams, and a clear read on exactly which
        topics still need work — built for the NMCN licensing exam.
      </p>

      <PulseTrace className="my-10 h-16 w-full max-w-md" />

      <div className="flex gap-4">
        <Link
          href="/signup"
          className="rounded-md bg-vital-teal px-6 py-3 font-body font-medium text-chart-cream transition hover:bg-ink-navy focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-vital-teal"
        >
          Create your account
        </Link>
        <Link
          href="/login"
          className="rounded-md border border-mist px-6 py-3 font-body font-medium text-ink-navy transition hover:border-vital-teal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-vital-teal"
        >
          Log in
        </Link>
      </div>
    </main>
  );
}
