"use client";

import { useState } from "react";
import type { Buyer } from "@/app/(dashboard)/search/page";
import { formatCurrency, formatDate, daysSince } from "@/lib/utils";
import {
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Phone,
  Mail,
  MapPin,
  Building2,
  Flame,
  FileText,
} from "lucide-react";

const RANK_COLORS = [
  "bg-yellow-500 text-slate-900",   // 1
  "bg-slate-400 text-slate-900",   // 2
  "bg-amber-700 text-white",       // 3
];

export function BuyerCard({ rank, buyer }: { rank: number; buyer: Buyer }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const days = daysSince(buyer.last_purchase);
  const isHot = buyer.purchase_count >= 3 && days !== null && days <= 90;

  function copyContact() {
    const phones = buyer.contacts.map((c) => c.phone).filter(Boolean).join(", ");
    const emails = buyer.contacts.map((c) => c.email).filter(Boolean).join(", ");
    const text = [buyer.name, phones, emails].filter(Boolean).join("\n");
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  const rankBg = RANK_COLORS[rank - 1] ?? "bg-slate-800 text-slate-300";
  const hasContacts = buyer.contacts.length > 0 || buyer.registered_agent;

  return (
    <div className="group bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl overflow-hidden transition-colors">
      <div className="p-4 sm:p-5">
        <div className="flex items-start gap-3">
          {/* Rank badge */}
          <div
            className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${rankBg}`}
          >
            {rank}
          </div>

          {/* Main content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold text-white text-sm leading-snug truncate">
                    {buyer.name}
                  </h3>
                  {isHot && (
                    <span className="flex items-center gap-1 bg-orange-950 text-orange-400 border border-orange-800/60 text-xs px-2 py-0.5 rounded-full flex-shrink-0">
                      <Flame size={9} fill="currentColor" />
                      Hot Buyer
                    </span>
                  )}
                </div>

                {/* Stats row */}
                <div className="flex items-center gap-4 mt-2 flex-wrap">
                  <StatPill
                    value={String(buyer.purchase_count)}
                    label={buyer.purchase_count === 1 ? "purchase" : "purchases"}
                    accent
                  />
                  <StatPill value={formatDate(buyer.last_purchase)} label="last buy" />
                  <StatPill value={formatCurrency(buyer.avg_price)} label="avg price" />
                </div>
              </div>

              {/* Copy button */}
              <button
                onClick={copyContact}
                title="Copy contact info"
                className="flex-shrink-0 flex items-center gap-1.5 text-xs text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg px-3 py-2 transition-colors"
              >
                {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>

            {/* Contact + agent info */}
            {hasContacts && (
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                {buyer.registered_agent && (
                  <div className="bg-slate-800/60 border border-slate-700/40 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 text-slate-500 text-xs mb-1.5">
                      <Building2 size={10} />
                      <span>Registered Agent</span>
                    </div>
                    <p className="text-white text-xs font-medium leading-tight">
                      {buyer.registered_agent}
                    </p>
                    {buyer.agent_address && (
                      <p className="text-slate-500 text-xs mt-1 flex items-start gap-1">
                        <MapPin size={9} className="mt-0.5 flex-shrink-0" />
                        <span>{buyer.agent_address}</span>
                      </p>
                    )}
                  </div>
                )}

                {buyer.contacts.length > 0 && (
                  <div className="bg-slate-800/60 border border-slate-700/40 rounded-lg p-3">
                    <div className="text-slate-500 text-xs mb-1.5">Contact Info</div>
                    <div className="space-y-1">
                      {buyer.contacts.slice(0, 2).map((c, i) => (
                        <div key={i} className="space-y-0.5">
                          {c.phone && (
                            <div className="flex items-center gap-1.5">
                              <Phone size={10} className="text-slate-500 flex-shrink-0" />
                              <span className="text-white text-xs">{c.phone}</span>
                              <SourceBadge label={c.source} />
                            </div>
                          )}
                          {c.email && (
                            <div className="flex items-center gap-1.5">
                              <Mail size={10} className="text-slate-500 flex-shrink-0" />
                              <span className="text-white text-xs truncate">{c.email}</span>
                              {!c.phone && <SourceBadge label={c.source} />}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Deed records toggle */}
      {buyer.transactions?.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-center gap-2 text-xs text-slate-500 hover:text-slate-300 py-2.5 border-t border-slate-800 hover:bg-slate-800/30 transition-colors"
          >
            <FileText size={11} />
            {expanded
              ? "Hide deed records"
              : `${buyer.transactions.length} deed record${buyer.transactions.length !== 1 ? "s" : ""}`}
            {expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
          </button>

          {expanded && (
            <div className="border-t border-slate-800 bg-slate-900/50 divide-y divide-slate-800/50">
              {buyer.transactions.map((t, i) => (
                <div key={i} className="px-5 py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-white truncate">{t.property_address || "—"}</p>
                    <p className="text-xs text-slate-500 mt-0.5 truncate">
                      from {t.grantor_name}
                      {t.deed_type ? ` · ${t.deed_type}` : ""}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs font-medium text-white">
                      {formatCurrency(t.sale_price)}
                    </p>
                    <p className="text-xs text-slate-500">{formatDate(t.sale_date)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function StatPill({
  value,
  label,
  accent,
}: {
  value: string;
  label: string;
  accent?: boolean;
}) {
  return (
    <div className="flex items-baseline gap-1">
      <span className={`text-sm font-semibold ${accent ? "text-blue-400" : "text-white"}`}>
        {value}
      </span>
      <span className="text-slate-500 text-xs">{label}</span>
    </div>
  );
}

function SourceBadge({ label }: { label: string }) {
  const map: Record<string, string> = {
    batchdata:      "text-blue-400 bg-blue-950 border-blue-800/60",
    propstream:     "text-purple-400 bg-purple-950 border-purple-800/60",
    dealmachine:    "text-orange-400 bg-orange-950 border-orange-800/60",
    opencorporates: "text-slate-400 bg-slate-800 border-slate-700",
  };
  const cls = map[label.toLowerCase()] ?? "text-slate-400 bg-slate-800 border-slate-700";
  return (
    <span className={`text-[10px] border px-1.5 py-0.5 rounded-full flex-shrink-0 ${cls}`}>
      {label}
    </span>
  );
}
