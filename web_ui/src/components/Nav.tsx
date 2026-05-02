import Link from "next/link";
import { History, Settings, TerminalSquare } from "lucide-react";

export function Nav() {
  return (
    <header className="border-b border-line bg-shell/90">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <Link href="/" className="flex items-center gap-2 text-sm font-semibold tracking-wide">
          <TerminalSquare className="h-5 w-5 text-signal" />
          ZELASH
        </Link>
        <nav className="flex items-center gap-2">
          <Link className="rounded-md p-2 text-slate-300 hover:bg-white/5" href="/history" aria-label="History">
            <History className="h-5 w-5" />
          </Link>
          <Link className="rounded-md p-2 text-slate-300 hover:bg-white/5" href="/settings" aria-label="Settings">
            <Settings className="h-5 w-5" />
          </Link>
        </nav>
      </div>
    </header>
  );
}
