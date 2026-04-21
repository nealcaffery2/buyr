"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";

const EXAMPLES = [
  "11206 Cape Primrose San Antonio TX",
  "4821 Cedar Springs Dallas TX 75219",
  "1340 Peachtree St NE Atlanta GA 30309",
];

export function HeroSearch({
  onSearch,
  loading,
}: {
  onSearch: (address: string) => void;
  loading: boolean;
}) {
  const [address, setAddress] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (address.trim() && !loading) onSearch(address.trim());
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-white">Find Cash Buyers</h1>
        <p className="text-slate-400 text-sm mt-1">
          Enter any property address — we&apos;ll search county deed records and
          skip trace the top buyers who purchase from wholesalers.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search
              size={16}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none"
            />
            <input
              type="text"
              aria-label="Property address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              disabled={loading}
              placeholder="123 Main St, San Antonio TX"
              className="w-full h-12 bg-slate-900 border border-slate-700 hover:border-slate-600 focus:border-blue-500 rounded-xl pl-10 pr-4 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 disabled:opacity-50 transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !address.trim()}
            className="h-12 px-6 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl text-sm transition-colors shadow-lg shadow-blue-900/30 flex items-center gap-2 whitespace-nowrap"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Running...
              </>
            ) : (
              "Snipe Buyers"
            )}
          </button>
        </div>
      </form>

      {/* Example addresses */}
      {!loading && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-600 text-xs">Try:</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => { setAddress(ex); onSearch(ex); }}
              className="text-xs text-slate-500 hover:text-blue-400 transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
