"use client";

import { useState } from "react";
import { Loader2, Crosshair } from "lucide-react";
import { AddressAutocomplete } from "@/components/address-autocomplete";

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
  const hasPlacesKey = !!process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (address.trim() && !loading) onSearch(address.trim());
  }

  return (
    <div className="relative space-y-5">
      {/* Ambient gradient backdrop for depth */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-10 h-40 bg-gradient-to-b from-blue-600/10 via-blue-600/[0.02] to-transparent blur-2xl"
      />

      <div className="relative">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-slate-400">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
          </span>
          Live Deed Intel
        </div>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Find Cash Buyers
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-400">
          Enter any property address — we&apos;ll search county deed records and
          skip trace the top buyers who purchase from wholesalers.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="relative">
        <div className="flex flex-col gap-2 sm:flex-row">
          <AddressAutocomplete
            value={address}
            onChange={setAddress}
            onSelect={(addr) => {
              if (!loading) onSearch(addr);
            }}
            disabled={loading}
            placeholder={
              hasPlacesKey
                ? "Start typing an address…"
                : "123 Main St, San Antonio TX"
            }
          />
          <button
            type="submit"
            disabled={loading || !address.trim()}
            className="group relative h-12 whitespace-nowrap rounded-xl bg-gradient-to-b from-blue-500 to-blue-600 px-6 text-sm font-semibold text-white shadow-lg shadow-blue-900/40 transition-all hover:from-blue-400 hover:to-blue-500 hover:shadow-blue-900/60 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:from-blue-500 disabled:hover:to-blue-600"
          >
            <span className="flex items-center gap-2">
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Running…
                </>
              ) : (
                <>
                  <Crosshair
                    size={14}
                    className="transition-transform group-hover:rotate-90"
                  />
                  Snipe Buyers
                </>
              )}
            </span>
          </button>
        </div>
      </form>

      {/* Example addresses */}
      {!loading && (
        <div className="relative flex flex-wrap items-center gap-x-3 gap-y-2">
          <span className="text-[11px] font-medium uppercase tracking-wider text-slate-600">
            Try
          </span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => {
                setAddress(ex);
                onSearch(ex);
              }}
              className="rounded-md border border-slate-800 bg-slate-900/50 px-2.5 py-1 text-xs text-slate-400 transition-colors hover:border-slate-700 hover:bg-slate-800 hover:text-blue-300"
            >
              {ex}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
