"use client";

import { useState, useEffect, useRef } from "react";
import { createBrowserClient } from "@/lib/supabase/client";
import { HeroSearch } from "@/components/hero-search";
import { PipelineStatus } from "@/components/pipeline-status";
import { BuyerCard } from "@/components/buyer-card";
import { exportToCsv } from "@/lib/utils";
import { Download, Users } from "lucide-react";

export type Buyer = {
  name: string;
  purchase_count: number;
  last_purchase: string | null;
  avg_price: number | null;
  score: number;
  registered_agent: string | null;
  agent_address: string | null;
  contacts: Array<{
    name: string;
    phone: string | null;
    email: string | null;
    source: string;
    confidence: number;
  }>;
  transactions: Array<{
    grantor_name: string;
    property_address: string;
    sale_date: string;
    sale_price: number | null;
    deed_type: string | null;
  }>;
};

type SearchState = "idle" | "running" | "done" | "error";

type ProgressRow = {
  step: string;
  percent: number;
  results?: Buyer[];
  error?: string;
};

export default function SearchPage() {
  const supabase = createBrowserClient();
  const [searchId, setSearchId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressRow | null>(null);
  const [buyers, setBuyers] = useState<Buyer[]>([]);
  const [state, setState] = useState<SearchState>("idle");
  const [searchedAddress, setSearchedAddress] = useState("");
  const channelRef = useRef<ReturnType<typeof supabase.channel> | null>(null);

  useEffect(() => {
    if (!searchId) return;
    channelRef.current = supabase
      .channel(`search:${searchId}`)
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "searches", filter: `id=eq.${searchId}` },
        (payload) => {
          const row = payload.new as ProgressRow;
          setProgress(row);
          if (row.step === "complete" && row.results) {
            setBuyers(row.results);
            setState("done");
          }
          if (row.step === "error") setState("error");
        }
      )
      .subscribe();
    return () => { channelRef.current?.unsubscribe(); };
  }, [searchId, supabase]);

  async function handleSearch(address: string) {
    setState("running");
    setBuyers([]);
    setProgress(null);
    setSearchedAddress(address);

    const { data: row, error } = await supabase
      .from("searches")
      .insert({ input_address: address, step: "queued", percent: 0 })
      .select("id")
      .single();

    if (error || !row) { setState("error"); return; }
    setSearchId(row.id);

    const scraperUrl = process.env.NEXT_PUBLIC_SCRAPER_API_URL;
    if (!scraperUrl) {
      // Dev mode: simulate progress for UI testing
      simulateProgress();
      return;
    }

    const res = await fetch(`${scraperUrl}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address, search_id: row.id }),
    });
    if (!res.ok) setState("error");
  }

  // UI preview mode when scraper isn't deployed yet
  function simulateProgress() {
    const steps = [
      { step: "parsing_address", percent: 15 },
      { step: "finding_wholesalers", percent: 25 },
      { step: "searching_county_records", percent: 45 },
      { step: "ranking_buyers", percent: 60 },
      { step: "opencorporates_lookup", percent: 75 },
      { step: "skip_tracing", percent: 88 },
      { step: "complete", percent: 100 },
    ];
    let i = 0;
    const tick = () => {
      if (i >= steps.length) return;
      setProgress(steps[i] as ProgressRow);
      if (steps[i].step === "complete") setState("done");
      i++;
      if (i < steps.length) setTimeout(tick, 900);
    };
    setTimeout(tick, 600);
  }

  return (
    <div className="space-y-10">
      {/* Hero search */}
      <HeroSearch onSearch={handleSearch} loading={state === "running"} />

      {/* Pipeline progress */}
      {state === "running" && progress && (
        <div className="animate-fade-in">
          <PipelineStatus step={progress.step} percent={progress.percent} />
        </div>
      )}

      {/* Error */}
      {state === "error" && (
        <div className="animate-fade-up bg-red-950/40 border border-red-800 text-red-300 rounded-xl px-5 py-4 text-sm">
          Something went wrong. Check your Supabase connection and scraper URL, then try again.
        </div>
      )}

      {/* Results */}
      {state === "done" && buyers.length > 0 && (
        <div className="space-y-5 animate-fade-in">
          {/* Results header bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-600/30">
                <Users size={16} className="text-blue-400" />
              </div>
              <div>
                <p className="text-white font-semibold text-sm">
                  {buyers.length} Buyers Found
                </p>
                <p className="text-slate-500 text-xs truncate max-w-xs">
                  {searchedAddress}
                </p>
              </div>
            </div>
            <button
              onClick={() => exportToCsv(buyers, "buyr-results")}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg px-4 py-2 transition-colors shadow-lg shadow-blue-900/30"
            >
              <Download size={14} />
              Export CSV
            </button>
          </div>

          {/* Cards */}
          <div className="space-y-3">
            {buyers.map((buyer, i) => (
              <div
                key={buyer.name}
                className="animate-fade-up"
                style={{ animationDelay: `${Math.min(i, 9) * 60}ms` }}
              >
                <BuyerCard rank={i + 1} buyer={buyer} />
              </div>
            ))}
          </div>
        </div>
      )}

      {state === "done" && buyers.length === 0 && (
        <div className="animate-fade-up text-center py-16">
          <p className="text-slate-500 text-sm">
            No buyers found for this market yet. Try a different address or add more wholesalers in Settings.
          </p>
        </div>
      )}
    </div>
  );
}
