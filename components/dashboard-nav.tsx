"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createBrowserClient } from "@/lib/supabase/client";
import type { User } from "@supabase/supabase-js";
import { Search, Settings, LogOut } from "lucide-react";

export function DashboardNav({ user }: { user: User }) {
  const pathname = usePathname();
  const router = useRouter();
  const supabase = createBrowserClient();

  async function signOut() {
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  const links = [
    { href: "/search", label: "Search", icon: Search },
    { href: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <nav className="border-b border-slate-800 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <span className="text-white font-bold text-lg">Buyr</span>
          {links.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-1.5 text-sm transition-colors ${
                pathname === href
                  ? "text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Icon size={14} />
              {label}
            </Link>
          ))}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-500 text-xs">{user.email}</span>
          <button
            onClick={signOut}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </nav>
  );
}
