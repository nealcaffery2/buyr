"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Settings, Zap } from "lucide-react";

const LINKS = [
  { href: "/search", label: "Search", icon: Search },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl supports-[backdrop-filter]:bg-slate-950/60">
      <div className="relative mx-auto flex h-14 max-w-5xl items-center gap-6 px-4">
        <Link
          href="/search"
          className="group flex items-center gap-2"
          aria-label="Buyr home"
        >
          <div className="relative flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-900/40 transition-transform group-hover:scale-105">
            <Zap size={14} className="text-white" fill="white" />
            <div className="absolute inset-0 rounded-lg ring-1 ring-white/10" />
          </div>
          <span className="bg-gradient-to-r from-white to-slate-300 bg-clip-text text-base font-bold tracking-tight text-transparent">
            Buyr
          </span>
        </Link>

        <div className="flex items-center gap-1">
          {LINKS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`relative flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition-colors ${
                  active
                    ? "text-white"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
                }`}
              >
                <Icon size={13} />
                {label}
                {active && (
                  <span className="absolute inset-0 -z-10 rounded-lg bg-slate-800 ring-1 ring-slate-700/80" />
                )}
              </Link>
            );
          })}
        </div>

        <div className="ml-auto hidden items-center gap-2 text-[11px] font-medium text-slate-500 sm:flex">
          <span className="inline-flex h-6 items-center rounded border border-slate-800 bg-slate-900/60 px-2 font-mono text-[10px] tracking-wide text-slate-400">
            v0.1
          </span>
        </div>
      </div>
    </nav>
  );
}
