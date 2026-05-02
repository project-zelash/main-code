import Link from "next/link";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-shell p-6 text-center">
      <section>
        <h1 className="text-3xl font-semibold">Build view not found</h1>
        <Link href="/" className="mt-5 inline-block rounded-md bg-cyan-300 px-4 py-2 font-semibold text-slate-950">Start a build</Link>
      </section>
    </main>
  );
}
