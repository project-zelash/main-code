export function LogPanel({ logs }: { logs: string[] }) {
  return (
    <section className="h-[420px] overflow-auto rounded-md border border-line bg-black/40 p-4 font-mono text-xs leading-6 text-cyan-100">
      {logs.length === 0 ? (
        <p className="text-slate-500">Waiting for agent output...</p>
      ) : (
        logs.map((line, index) => <p key={`${line}-${index}`}>{line}</p>)
      )}
    </section>
  );
}
