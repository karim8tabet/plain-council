import type { Metadata } from "next";
import { Geist } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "Plain Council", template: "%s · Plain Council" },
  description: "Toronto council decisions in plain language: what is proposed, who it affects, and when you can have a say.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:m-2 focus:p-2 focus:bg-card">
          Skip to main content
        </a>
        <header className="border-b border-line bg-card no-print">
          <div className="mx-auto max-w-3xl px-4 py-3 flex items-center justify-between gap-4">
            <Link href="/" className="font-semibold text-ink no-underline text-lg">Plain Council</Link>
            <nav className="text-sm flex gap-4">
              <Link href="/items">All items</Link>
              <Link href="/about">How this works</Link>
            </nav>
          </div>
        </header>
        <main id="main" className="flex-1 mx-auto w-full max-w-3xl px-4 py-8">{children}</main>
        <footer className="border-t border-line text-sm text-muted no-print">
          <div className="mx-auto max-w-3xl px-4 py-6 space-y-2">
            <p>
              Plain Council is an independent prototype, not an official City of Toronto service. Every sentence links
              to the official record it comes from. If anything here differs from the official record, the official record is correct.
            </p>
            <p>Sources: City of Toronto council meeting system (TMMIS) and Toronto Open Data.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
