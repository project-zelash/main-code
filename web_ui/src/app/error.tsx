"use client";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <main className="grid min-h-screen place-items-center bg-shell p-6 text-center">
      <section className="max-w-lg rounded-md border border-line bg-panel p-6">
        <h1 className="text-2xl font-semibold">Something failed</h1>
        <p className="mt-3 text-sm text-slate-400">{error.message}</p>
        <button onClick={reset} className="mt-5 rounded-md bg-cyan-300 px-4 py-2 font-semibold text-slate-950">Retry</button>
      </section>
    </main>
  );
}
