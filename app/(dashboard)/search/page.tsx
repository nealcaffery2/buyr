"use client";

import { useState, useEffect, useRef } from "react";
import { createBrowserClient } from "@/lib/supabase/client";
import { SearchBar } from "@/components/search-bar";
import { ProgressStepper } from "@/components/progress-stepper";
import { BuyerCard } from "@/components/buyer-card";
import { exportToCsv } from "@/lib/utils";
import { Download } from "lucide-react";

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

type ProgressState = {
  step: string;
  percent: number;
  results?: Buyer[];
};

const STEP_LABELS: Record<string, string> = {
  parsing_address: "Parsing address",
  finding_wholesalers: "Finding wholesaler LLCs",
  searching_county_records: "Searching county deed records",
  ranking_buyers: "Ranking top buyers",
  opencorporates_lookup: "Looking up registered agents",
  skip_tracing: "Skip tracing contacts",
  complete: "Complete",
};

export default function SearchPage() {
  const supabase = createBrowserClient();
  const [searchId, setSearchId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const [buyers, setBuyers] = useState<Buyer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const channelRef = useRef<ReturnType<typeof supabase.channel> | null>(null);

  useEffect(() => {
    if (!searchId) return;

    channelRef.current = supabase
      .channel(`search:${searchId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "searches",
          filter: `id=eq.${searchId}`,
        },
        (payload) => {
          const row = payload.new as Record<string, unknown>;
          const step = row.step as string;
          const percent = row.percent as number;
          const results = row.results as Buyer[] | undefined;
          setProgress({ step, percent, results });
          if (step === "complete" && results) {
            setBuyers(results);
            setLoading(false);
          }
          if (step === "error") {
            setError((row.error as string) || "Search failed");
            setLoading(false);
          }
        }
      )
      .subscribe();

    return () => {
      channelRef.current?.unsubscribe();
    };
  }, [searchId, supabase]);

  async function handleSearch(address: string) {
    setLoading(true);
    setError(null);
    setBuyers([]);
    setProgress(null);

    const { data: searchRow, error: insertErr } = await supabase
      .from("searches")
      .insert({ input_address: address, step: "queued", percent: 0 })
      .select("id")
      .single();

    if (insertErr || !searchRow) {
      setError("Failed to start search. Check Supabase connection.");
      setLoading(false);
      return;
    }

    setSearchId(searchRow.id);

    const res = await fetch(
      `${process.env.NEXT_PUBLIC_SCRAPER_API_URL}/api/search`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          address,
          search_id: searchRow.id,
        }),
      }
    );

    if (!res.ok) {
      setError("Scraper service unreachable. Is Railway deployed?");
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Snipe Buyers</h1>
        <p className="text-slate-400 text-sm">
          Enter any property address to find the top 10 cash buyers that
          purchase from wholesalers in that market.
        </p>
      </div>

      <SearchBar onSearch={handleSearch} loading={loading} />

      {error && (
        <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {loading && progress && (
        <ProgressStepper
          currentStep={progress.step}
          percent={progress.percent}
          stepLabels={STEP_LABELS}
        />
      )}

      {buyers.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">
              Top {buyers.length} Buyers Found
            </h2>
            <button
              onClick={() => exportToCsv(buyers, "buyr-results")}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 rounded-md px-3 py-1.5 transition-colors"
            >
              <Download size={14} />
              Export CSV
            </button>
          </div>
          <div className="space-y-4">
            {buyers.map((buyer, i) => (
              <BuyerCard key={buyer.name} rank={i + 1} buyer={buyer} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
