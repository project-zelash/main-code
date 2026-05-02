"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Nav } from "@/components/Nav";
import { api, BuildStatus } from "@/lib/api";

export default function HistoryPage() {
  const [builds, setBuilds] = useState<BuildStatus[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listBuilds().then((data) => setBuilds(data.builds)).catch((err) => setError(err instanceof Error ? err.message : "Unable to load history."));
  }, []);

  return (
    <main className="min-h-screen bg-shell">
      <Nav />
      <section className="mx-auto max-w-6xl px-5 py-8">
        <h1 className="text-4xl font-semibold">Build history</h1>
        {error && <div className="mt-5 rounded-md border border-red-500/40 bg-red-500/10 p-4 text-red-100">{error}</div>}
        <div className="mt-6 overflow-hidden rounded-md border border-line">
          {builds.length === 0 ? (
            <div className="bg-panel p-8 text-slate-400">No previous builds.</div>
          ) : (
            builds.map((build) => (
              <Link key={build.build_id} href={build.status === "completed" ? `/results/${build.build_id}` : `/build/${build.build_id}`} className="grid gap-2 border-b border-line bg-panel p-4 hover:bg-white/5 md:grid-cols-[1fr_130px_220px]">
                <span className="truncate text-sm">{build.prompt}</span>
                <span className="text-sm uppercase text-slate-400">{build.status}</span>
                <span className="text-sm text-slate-500">{build.created_at_iso}</span>
              </Link>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
