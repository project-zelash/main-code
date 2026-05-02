"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { Nav } from "@/components/Nav";
import { api } from "@/lib/api";

const examples = [
  "Build a SaaS dashboard for tracking gym memberships.",
  "Create a shoe website with product cards and checkout flow.",
  "Build a local-first CRM for freelancers.",
  "Create a restaurant ordering site with admin inventory."
];

export default function HomePage() {
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function submit() {
    setError("");
    if (!prompt.trim()) {
      setError("Enter a build goal.");
      return;
    }
    setLoading(true);
    try {
      const build = await api.startBuild(prompt);
      router.push(`/build/${build.build_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start build.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen scanline">
      <Nav />
      <section className="mx-auto flex min-h-[calc(100vh-70px)] max-w-5xl flex-col justify-center px-5 py-12">
        <div className="mb-8 max-w-3xl">
          <p className="mb-4 text-xs font-semibold uppercase tracking-[0.22em] text-signal">Autonomous build control</p>
          <h1 className="text-5xl font-semibold leading-tight text-white md:text-7xl">Tell Zelash what to build.</h1>
        </div>
        <div className="rounded-md border border-line bg-panel p-4">
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="I want to build a SaaS dashboard for tracking gym memberships."
            className="min-h-40 w-full resize-none bg-transparent p-3 text-xl outline-none placeholder:text-slate-600"
          />
          <div className="flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-red-300">{error}</p>
            <button
              onClick={submit}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-md bg-cyan-300 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Starting..." : "Submit"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {examples.map((example) => (
            <button key={example} onClick={() => setPrompt(example)} className="rounded-md border border-line px-3 py-2 text-sm text-slate-300 hover:bg-white/5">
              {example}
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
