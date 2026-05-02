"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Copy, Download, RotateCcw } from "lucide-react";
import { Nav } from "@/components/Nav";
import { api, BuildResult } from "@/lib/api";

export default function ResultsPage({ params }: { params: { id: string } }) {
  const [result, setResult] = useState<BuildResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getResult(params.id).then(setResult).catch((err) => setError(err instanceof Error ? err.message : "Result unavailable."));
  }, [params.id]);

  return (
    <main className="min-h-screen bg-shell">
      <Nav />
      <section className="mx-auto max-w-6xl px-5 py-8">
        <p className="text-xs uppercase tracking-[0.2em] text-signal">Build result</p>
        <h1 className="mt-2 text-4xl font-semibold">Deployment ready</h1>
        {error && <div className="mt-6 rounded-md border border-amber-500/40 bg-amber-500/10 p-4 text-amber-100">{error}</div>}
        {result && (
          <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_420px]">
            <div className="space-y-4">
              <div className="rounded-md border border-line bg-panel p-5">
                <p className="text-sm text-slate-400">Live URL</p>
                <a className="mt-2 block break-all text-xl font-semibold text-cyan-200" href={result.live_url} target="_blank">
                  {result.live_url}
                </a>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button onClick={() => navigator.clipboard.writeText(result.live_url)} className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm hover:bg-white/5">
                    <Copy className="h-4 w-4" /> Copy URL
                  </button>
                  <button className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm text-slate-500" disabled>
                    <Download className="h-4 w-4" /> Download ZIP
                  </button>
                  <Link href="/" className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm hover:bg-white/5">
                    <RotateCcw className="h-4 w-4" /> New build
                  </Link>
                </div>
              </div>
              <div className="rounded-md border border-line bg-panel p-5">
                <h2 className="font-semibold">Files created</h2>
                <div className="mt-3 grid gap-2 text-sm text-slate-300">
                  {result.files_created.map((file) => <code key={file} className="rounded bg-black/30 px-2 py-1">{file}</code>)}
                </div>
              </div>
            </div>
            <aside className="space-y-4">
              <div className="rounded-md border border-line bg-panel p-5">
                <h2 className="font-semibold">Tech stack</h2>
                <div className="mt-3 flex flex-wrap gap-2">
                  {result.tech_stack.map((item) => <span key={item} className="rounded-md bg-cyan-300/10 px-2 py-1 text-sm text-cyan-100">{item}</span>)}
                </div>
              </div>
              <div className="rounded-md border border-line bg-panel p-5">
                <h2 className="font-semibold">Stage timing</h2>
                <div className="mt-3 space-y-2 text-sm">
                  {Object.entries(result.stage_durations).map(([name, duration]) => (
                    <div key={name} className="flex justify-between gap-4 text-slate-300">
                      <span>{name}</span>
                      <span>{duration ?? 0}s</span>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </div>
        )}
      </section>
    </main>
  );
}
