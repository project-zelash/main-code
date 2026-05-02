import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Zelash Mission Control",
  description: "Autonomous project synthesis dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-shell font-sans text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
