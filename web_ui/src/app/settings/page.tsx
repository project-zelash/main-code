"use client";

import { useState } from "react";
import { Nav } from "@/components/Nav";

export default function SettingsPage() {
  const [provider, setProvider] = useState("gemini");

  return (
    <main className="min-h-screen bg-shell">
      <Nav />
      <section className="mx-auto max-w-4xl px-5 py-8">
        <h1 className="text-4xl font-semibold">Settings</h1>
        <div className="mt-6 space-y-5 rounded-md border border-line bg-panel p-5">
          <label className="block">
            <span className="text-sm text-slate-400">LLM provider</span>
            <select value={provider} onChange={(event) => setProvider(event.target.value)} className="mt-2 w-full rounded-md border border-line bg-shell p-3">
              <option value="gemini">Gemini</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="bedrock">AWS Bedrock</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm text-slate-400">API key</span>
            <input type="password" placeholder="Stored in backend .env" className="mt-2 w-full rounded-md border border-line bg-shell p-3" />
          </label>
          <label className="block">
            <span className="text-sm text-slate-400">Deployment preference</span>
            <select className="mt-2 w-full rounded-md border border-line bg-shell p-3">
              <option>Local static URL</option>
              <option disabled>External provider</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm text-slate-400">Pipeline timeout seconds</span>
            <input type="number" defaultValue={300} className="mt-2 w-full rounded-md border border-line bg-shell p-3" />
          </label>
          <button className="rounded-md bg-cyan-300 px-4 py-3 font-semibold text-slate-950 hover:bg-cyan-200">Save settings</button>
        </div>
      </section>
    </main>
  );
}
